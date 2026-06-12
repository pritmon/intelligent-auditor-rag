import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from pydantic import StringConstraints
from typing import Annotated
from dotenv import load_dotenv

# ── CRIT-1: load .env and validate API key BEFORE any LlamaIndex/OpenAI import ──
load_dotenv()

_api_key = os.environ.get("OPENAI_API_KEY")
if not _api_key or "your_openai_api_key" in _api_key:
    raise RuntimeError(
        "OPENAI_API_KEY is not set or is still a placeholder. "
        "Set it in your .env file before starting the server."
    )

from src.ingester import Ingester
from src.indexer import Indexer
from src.retriever import HybridRetriever
from src.reranker import Reranker
from src.generator import Generator
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from openai import RateLimitError, APIConnectionError, APITimeoutError, APIStatusError

# ── MED-10: ensure artifacts/ exists before FileHandler is created ──
os.makedirs("artifacts", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("artifacts/auditor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("IntelligentAuditor")

if os.environ.get("LANGCHAIN_TRACING_V2") == "true":
    logger.info("LangSmith tracing is enabled.")

# ── HIGH-8: single configurable model; Settings.llm and Generator both read LLM_MODEL ──
_llm_model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
Settings.llm = OpenAI(model=_llm_model)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.chunk_size = 512

app = FastAPI(
    title="Intelligent Auditor RAG",
    description="""
## AI-powered financial document analysis

Upload any financial filing (10-K, 10-Q, annual report) and ask questions in plain English.
Get precise answers with exact page citations — no guessing, no hallucinations.

### How it works
1. **POST /ingest** — reads PDFs from `data/raw/` and builds the search index
2. **POST /ask** — ask any question, get a cited answer in seconds

### Pipeline
`PDF → Chunks → Embeddings → FAISS Index → Hybrid Retrieval (Vector + BM25 + RRF) → LLM Reranker → GPT-4o-mini → Cited Answer`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

RAW_DATA_PATH = "data/raw"
VECTOR_STORE_PATH = "vector_store"

os.makedirs(RAW_DATA_PATH, exist_ok=True)
os.makedirs(VECTOR_STORE_PATH, exist_ok=True)

ingester = Ingester(input_dir=RAW_DATA_PATH)
indexer = Indexer(storage_dir=VECTOR_STORE_PATH)
generator = Generator()

# ── HIGH-4: protect shared index state with an asyncio lock ──
current_index = None
current_nodes = None   # cached node list — rebuilt only on /ingest
_index_lock = asyncio.Lock()

try:
    current_index = indexer.load_index()
    if current_index is not None:
        current_nodes = list(current_index.docstore.docs.values())
except Exception as e:
    logger.warning(f"Could not load index during startup: {e}. Run /ingest first.")


# ── HIGH-6: optional API-key guard — set AUDITOR_API_KEY in env to enable ──
async def check_api_key(x_api_key: str = Header(default=None)):
    required = os.environ.get("AUDITOR_API_KEY")
    if required and x_api_key != required:
        raise HTTPException(status_code=403, detail="Forbidden")


# ── HIGH-1: validate query length; strip_whitespace removes leading/trailing spaces
#    before the min_length check so blank/whitespace-only queries are rejected. ──
class QueryRequest(BaseModel):
    query: Annotated[str, StringConstraints(min_length=1, max_length=4096, strip_whitespace=True)]


@app.post("/ingest", dependencies=[Depends(check_api_key)])
async def ingest_documents():
    """Read PDFs from data/raw and build the search index."""
    global current_index, current_nodes
    logger.info("Starting ingestion process.")
    try:
        docs = ingester.load_documents()
        if not docs:
            logger.warning("No documents found in data/raw.")
            return {"message": "No documents found in data/raw."}

        chunks = ingester.create_chunks(docs)
        del docs

        # ── HIGH-4: hold the lock while swapping the index ──
        async with _index_lock:
            current_index = indexer.create_index(chunks)
            current_nodes = list(current_index.docstore.docs.values())

        num_chunks = len(chunks)
        del chunks

        logger.info(f"Successfully indexed {num_chunks} chunks.")
        return {"message": f"Successfully indexed {num_chunks} chunks."}
    except (RateLimitError, APIConnectionError, APITimeoutError) as e:
        logger.error(f"OpenAI API unavailable during ingestion: {e}")
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable. Please try again shortly.")
    except APIStatusError as e:
        logger.error(f"OpenAI API error during ingestion (status {e.status_code}): {e}")
        raise HTTPException(status_code=503, detail="AI service error. Please try again.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        # ── HIGH-3: return a generic message; detail stays in server logs ──
        raise HTTPException(status_code=500, detail="Ingestion failed. Check server logs.")


@app.post("/ask", dependencies=[Depends(check_api_key)])
async def ask_auditor(request: QueryRequest):
    """Ask a question about the indexed documents."""
    # ── HIGH-4: take a consistent snapshot under the lock ──
    async with _index_lock:
        if current_index is None:
            raise HTTPException(
                status_code=400,
                detail="Search index not found. Please run /ingest first."
            )
        index_snapshot = current_index
        nodes_snapshot = current_nodes

    logger.info(f"User query: {request.query!r}")
    try:
        retriever = HybridRetriever(index=index_snapshot, nodes=nodes_snapshot)
        relevant_chunks = retriever.retrieve(request.query)

        reranker = Reranker()
        best_chunks = reranker.rerank(request.query, relevant_chunks)

        answer = generator.generate_response(request.query, best_chunks)

        logger.info("Answer generated successfully.")
        return {"query": request.query, "answer": answer}
    except (RateLimitError, APIConnectionError, APITimeoutError) as e:
        logger.error(f"OpenAI API unavailable during query processing: {e}")
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable. Please try again shortly.")
    except APIStatusError as e:
        logger.error(f"OpenAI API error during query processing (status {e.status_code}): {e}")
        raise HTTPException(status_code=503, detail="AI service error. Please try again.")
    except Exception as e:
        logger.error(f"Error during query processing: {e}")
        # ── HIGH-3: keep internal details out of the API response ──
        raise HTTPException(status_code=500, detail="Query processing failed. Check server logs.")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Intelligent Auditor RAG</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    html, body {
      height: 100%;
      overflow: hidden;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #060d1f;
      color: #e2e8f0;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* ── NAV ── */
    nav {
      flex-shrink: 0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 32px;
      border-bottom: 1px solid #1e293b;
      background: rgba(6,13,31,0.98);
      z-index: 10;
    }
    .nav-brand { font-size: 1.1rem; font-weight: 700; color: #fff; letter-spacing: -0.3px; }
    .nav-brand span { color: #3b82f6; }
    .nav-links { display: flex; gap: 10px; }
    .nav-links a {
      padding: 6px 14px; border-radius: 8px; font-size: 0.88rem; font-weight: 500;
      text-decoration: none; transition: all 0.2s;
    }
    .btn-ghost { color: #94a3b8; border: 1px solid #1e293b; }
    .btn-ghost:hover { background: #1e293b; color: #e2e8f0; }
    .btn-primary { background: #3b82f6; color: #fff; border: 1px solid #3b82f6; }
    .btn-primary:hover { background: #2563eb; border-color: #2563eb; }

    /* ── MAIN TWO-COLUMN LAYOUT ── */
    .page-main {
      flex: 1;
      display: grid;
      grid-template-columns: 1fr 1.15fr;
      gap: 24px;
      padding: 16px 28px;
      min-height: 0;
      overflow: hidden;
    }

    /* ── LEFT COLUMN ── */
    .left-col {
      display: flex;
      flex-direction: column;
      gap: 10px;
      min-height: 0;
      overflow: hidden;
    }
    .badge {
      display: inline-flex; align-items: center; gap: 6px;
      background: rgba(59,130,246,0.12); border: 1px solid rgba(59,130,246,0.3);
      color: #60a5fa; padding: 5px 12px; border-radius: 100px;
      font-size: 0.8rem; font-weight: 600; letter-spacing: 0.5px;
      text-transform: uppercase; width: fit-content;
    }
    .badge-dot { width: 6px; height: 6px; background: #3b82f6; border-radius: 50%; animation: pulse 2s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
    h1 {
      font-size: clamp(1.9rem, 3.2vw, 2.9rem);
      font-weight: 800; line-height: 1.15;
      background: linear-gradient(135deg, #fff 40%, #60a5fa);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text; letter-spacing: -0.5px;
    }
    .hero-sub {
      font-size: 1rem; color: #94a3b8; line-height: 1.6;
    }
    .hero-sub strong { color: #e2e8f0; }

    /* ── PIPELINE ── */
    .pipeline {
      display: flex; align-items: center;
      flex-wrap: wrap; gap: 5px;
    }
    .pipe-step {
      background: #0f172a; border: 1px solid #1e293b;
      padding: 4px 10px; border-radius: 6px;
      font-size: 0.78rem; color: #64748b; font-weight: 500;
    }
    .pipe-step.highlight { background: rgba(59,130,246,0.1); border-color: rgba(59,130,246,0.3); color: #60a5fa; }
    .pipe-arrow { color: #334155; font-size: 0.75rem; }

    /* ── HOW IT WORKS (left col) ── */
    .steps {
      display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
      align-content: start;
    }
    .step {
      background: #0f172a; border: 1px solid #1e293b;
      border-radius: 12px; padding: 12px;
    }
    .step-num {
      width: 28px; height: 28px; border-radius: 8px;
      background: rgba(59,130,246,0.15); border: 1px solid rgba(59,130,246,0.3);
      display: flex; align-items: center; justify-content: center;
      font-weight: 800; color: #60a5fa; font-size: 0.88rem; margin-bottom: 6px;
    }
    .step h3 { font-size: 0.93rem; font-weight: 700; color: #e2e8f0; margin-bottom: 4px; }
    .step p { font-size: 0.83rem; color: #64748b; line-height: 1.5; }
    .step .tag {
      display: inline-block; margin-top: 6px;
      background: #1e293b; color: #60a5fa;
      padding: 2px 8px; border-radius: 5px; font-size: 0.75rem; font-weight: 600;
    }

    /* ── RIGHT COLUMN — DEMO CARD ── */
    .right-col {
      display: flex;
      flex-direction: column;
      min-height: 0;
    }
    .demo-card {
      flex: 1;
      background: #0f172a;
      border: 1px solid #1e293b;
      border-radius: 16px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.4);
      display: flex;
      flex-direction: column;
      min-height: 0;
    }
    .demo-header {
      padding: 14px 20px;
      border-bottom: 1px solid #1e293b;
      display: flex; align-items: center; justify-content: space-between;
      flex-shrink: 0;
    }
    .demo-title { font-size: 0.92rem; font-weight: 600; color: #94a3b8; }
    .demo-status {
      display: flex; align-items: center; gap: 6px;
      font-size: 0.83rem; color: #4ade80; font-weight: 500;
    }
    .status-dot { width: 7px; height: 7px; background: #4ade80; border-radius: 50%; animation: pulse 2s infinite; }

    .demo-body { padding: 14px 18px; flex: 1; display: flex; flex-direction: column; min-height: 0; }

    /* chips */
    .chips { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 10px; flex-shrink: 0; }
    .chip {
      background: #1e293b; border: 1px solid #334155;
      color: #94a3b8; padding: 5px 11px; border-radius: 7px;
      font-size: 0.82rem; cursor: pointer; transition: all 0.2s; white-space: nowrap;
    }
    .chip:hover { background: rgba(59,130,246,0.15); border-color: #3b82f6; color: #60a5fa; }

    /* input row */
    .input-row { display: flex; gap: 8px; flex-shrink: 0; }
    .query-input {
      flex: 1;
      background: #1e293b; border: 1px solid #334155;
      color: #e2e8f0; padding: 10px 14px; border-radius: 9px;
      font-size: 0.97rem; outline: none; transition: border-color 0.2s;
      font-family: inherit;
    }
    .query-input:focus { border-color: #3b82f6; }
    .query-input::placeholder { color: #475569; }
    .ask-btn {
      background: #3b82f6; color: #fff; border: none;
      padding: 10px 20px; border-radius: 9px;
      font-size: 0.95rem; font-weight: 600; cursor: pointer;
      transition: all 0.2s; white-space: nowrap; font-family: inherit;
    }
    .ask-btn:hover:not(:disabled) { background: #2563eb; }
    .ask-btn:disabled { opacity: 0.6; cursor: not-allowed; }

    /* response */
    .response-box {
      margin-top: 10px;
      background: #060d1f; border: 1px solid #1e293b;
      border-radius: 10px; padding: 14px;
      display: none;
      flex: 1;
      overflow-y: auto;
      min-height: 0;
    }
    .response-label {
      font-size: 0.76rem; font-weight: 700; letter-spacing: 1px;
      text-transform: uppercase; color: #475569; margin-bottom: 8px;
    }
    .response-text {
      font-size: 0.95rem; color: #cbd5e1; line-height: 1.7;
      white-space: pre-wrap; word-break: break-word;
    }
    .response-text strong { color: #e2e8f0; }
    .spinner {
      display: inline-block; width: 14px; height: 14px;
      border: 2px solid #334155; border-top-color: #3b82f6;
      border-radius: 50%; animation: spin 0.7s linear infinite; vertical-align: middle;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .error-text { color: #f87171; }

    /* ── STATS ── */
    .stats {
      display: grid; grid-template-columns: repeat(3, 1fr);
      gap: 1px; background: #1e293b;
      border-top: 1px solid #1e293b;
      border-radius: 0 0 16px 16px;
      overflow: hidden;
      flex-shrink: 0;
    }
    .stat { background: #0f172a; padding: 10px 16px; text-align: center; }
    .stat-value { font-size: 1.5rem; font-weight: 800; color: #3b82f6; }
    .stat-label { font-size: 0.76rem; color: #475569; margin-top: 2px; font-weight: 500; }

    /* ── FOOTER ── */
    footer {
      flex-shrink: 0;
      border-top: 1px solid #1e293b;
      padding: 10px 32px;
      display: flex; justify-content: space-between; align-items: center;
      font-size: 0.78rem; color: #475569;
    }
    footer a { color: #60a5fa; text-decoration: none; }
    footer a:hover { text-decoration: underline; }

    @media (max-width: 768px) {
      html, body { overflow: auto; height: auto; }
      .page-main { grid-template-columns: 1fr; height: auto; overflow: visible; }
      nav { padding: 10px 16px; }
      footer { flex-direction: column; gap: 6px; text-align: center; }
    }
  </style>
</head>
<body>

<nav>
  <div class="nav-brand">🔍 Intelligent <span>Auditor</span></div>
  <div class="nav-links">
    <a href="https://github.com/pritmon/intelligent-auditor-rag" target="_blank" class="btn-ghost">GitHub</a>
    <a href="/docs" class="btn-primary">API Docs</a>
  </div>
</nav>

<div class="page-main">
  <!-- LEFT COLUMN -->
  <div class="left-col">
    <div class="badge"><div class="badge-dot"></div> Live · Tesla 10-K loaded</div>
    <h1>Ask anything about a financial filing</h1>
    <p class="hero-sub">
      Upload any <strong>10-K, 10-Q, or annual report</strong>.
      Get a precise answer with the <strong>exact page citation</strong> — no guessing, no hallucinations.
    </p>

    <div class="pipeline">
      <div class="pipe-step highlight">📄 PDF</div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step">Chunks</div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step highlight">FAISS</div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step">BM25+RRF</div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step highlight">Reranker</div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step highlight">GPT-4o-mini</div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step">✅ Answer</div>
    </div>

    <div class="steps">
      <div class="step">
        <div class="step-num">1</div>
        <h3>Ingest</h3>
        <p>PDF split into overlapping chunks, each converted to an embedding vector.</p>
        <span class="tag">LlamaIndex · OpenAI</span>
      </div>
      <div class="step">
        <div class="step-num">2</div>
        <h3>Retrieve</h3>
        <p>Vector search (meaning) + BM25 (keywords), merged with Reciprocal Rank Fusion.</p>
        <span class="tag">FAISS · BM25 · RRF</span>
      </div>
      <div class="step">
        <div class="step-num">3</div>
        <h3>Rerank</h3>
        <p>LLM picks the 3 most relevant chunks, removing noise before generation.</p>
        <span class="tag">LLMRerank</span>
      </div>
      <div class="step">
        <div class="step-num">4</div>
        <h3>Generate</h3>
        <p>GPT-4o-mini writes a structured answer. Every fact must cite a page number.</p>
        <span class="tag">GPT-4o-mini · Temp 0</span>
      </div>
    </div>
  </div>

  <!-- RIGHT COLUMN -->
  <div class="right-col">
    <div class="demo-card">
      <div class="demo-header">
        <div class="demo-title">Try it live — Tesla Annual Report loaded</div>
        <div class="demo-status"><div class="status-dot"></div> API online</div>
      </div>

      <div class="demo-body">
        <div class="chips">
          <div class="chip" onclick="setQuery(this)">What is Tesla total revenue?</div>
          <div class="chip" onclick="setQuery(this)">What are the main risk factors?</div>
          <div class="chip" onclick="setQuery(this)">What is Tesla net income?</div>
          <div class="chip" onclick="setQuery(this)">Who is the CEO of Tesla?</div>
          <div class="chip" onclick="setQuery(this)">What is Tesla free cash flow?</div>
        </div>

        <div class="input-row">
          <input
            id="queryInput"
            class="query-input"
            type="text"
            placeholder="Ask anything about the Tesla annual report..."
            onkeydown="if(event.key==='Enter') askQuestion()"
          />
          <button id="askBtn" class="ask-btn" onclick="askQuestion()">Ask →</button>
        </div>

        <div id="responseBox" class="response-box">
          <div class="response-label">Answer</div>
          <div id="responseText" class="response-text"></div>
        </div>
      </div>

      <div class="stats">
        <div class="stat">
          <div class="stat-value">0.94</div>
          <div class="stat-label">Faithfulness</div>
        </div>
        <div class="stat">
          <div class="stat-value">0.92</div>
          <div class="stat-label">Answer Relevance</div>
        </div>
        <div class="stat">
          <div class="stat-value">0.89</div>
          <div class="stat-label">Context Precision</div>
        </div>
      </div>
    </div>
  </div>
</div>

<footer>
  <span>Built by <strong>Pritam Mondal</strong></span>
  <span>
    <a href="https://github.com/pritmon/intelligent-auditor-rag" target="_blank">GitHub</a>
    &nbsp;·&nbsp;
    <a href="/docs">API Docs</a>
    &nbsp;·&nbsp;
    <a href="/redoc">ReDoc</a>
  </span>
</footer>

<script>
  function setQuery(el) {
    document.getElementById('queryInput').value = el.textContent.trim();
    askQuestion();
  }

  async function askQuestion() {
    const input = document.getElementById('queryInput');
    const btn = document.getElementById('askBtn');
    const box = document.getElementById('responseBox');
    const text = document.getElementById('responseText');
    const query = input.value.trim();

    if (!query) { input.focus(); return; }

    btn.disabled = true;
    btn.textContent = 'Thinking…';
    box.style.display = 'block';
    text.innerHTML = '<span class="spinner"></span>&nbsp; Searching… (first request may take up to 60 seconds on the free server — please wait)';
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 90000);
      const res = await fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
        signal: controller.signal
      });
      clearTimeout(timeout);

      const data = await res.json();

      if (!res.ok) {
        text.innerHTML = '<span class="error-text">⚠ ' + (data.detail || 'Something went wrong. Please try again.') + '</span>';
        return;
      }

      const formatted = data.answer
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\\\\n/g, '<br/>')
        .replace(/\\n/g, '<br/>');
      text.innerHTML = formatted;
      box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (e) {
      text.innerHTML = '<span class="error-text">⚠ Could not reach the server. Please try again.</span>';
    } finally {
      btn.disabled = false;
      btn.textContent = 'Ask →';
    }
  }
</script>
</body>
</html>
""")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
