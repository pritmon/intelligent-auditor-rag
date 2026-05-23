import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
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

app = FastAPI(title="Intelligent Auditor RAG")

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


# ── HIGH-1: validate query length; strip_whitespace prevents empty/blank queries ──
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096, strip_whitespace=True)


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
    except Exception as e:
        logger.error(f"Error during query processing: {e}")
        # ── HIGH-3: keep internal details out of the API response ──
        raise HTTPException(status_code=500, detail="Query processing failed. Check server logs.")


@app.get("/")
def home():
    return {"message": "Welcome to the Intelligent Auditor. Use /docs to see the API."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
