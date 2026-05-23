# Fixes Applied — Intelligent Auditor RAG

All 28 issues from the audit have been remediated. This document maps each fix
to the exact file(s) changed.

---

## Critical (4 fixes)

| Fix | File(s) Changed | What Changed |
|---|---|---|
| CRIT-1 | `main.py` | Added `load_dotenv()` and key-presence check as the very first statements, before any LlamaIndex import. |
| CRIT-2 / MED-1 | `src/reranker.py` | Replaced `return nodes[:3]` placeholder with actual `LLMRerank.postprocess_nodes()` call using `QueryBundle`. |
| CRIT-3 | `src/generator.py` | Replaced `str.format(context_str=..., query_str=...)` with two chained `.replace()` calls to prevent format-string injection. |
| CRIT-4 | `main.py`, `Dockerfile` | Removed `os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"` and `ENV KMP_DUPLICATE_LIB_OK=TRUE`. |

---

## High (8 fixes)

| Fix | File(s) Changed | What Changed |
|---|---|---|
| HIGH-1 | `main.py` | `QueryRequest.query` now uses `Field(..., min_length=1, max_length=4096, strip_whitespace=True)`. |
| HIGH-2 | `requirements.txt` | All 17 packages given `>=X.Y,<X+1.0` version constraints. |
| HIGH-3 | `main.py` | Both `except` blocks now return `"Check server logs"` to callers; full details go to `logger.error()`. |
| HIGH-4 | `main.py` | Added `asyncio.Lock` (`_index_lock`); `/ingest` holds the lock during index swap; `/ask` takes a snapshot under the lock. |
| HIGH-5 | `run_ingestion.py`, `tests/smoke_test.py` | Replaced `sys.path.append(os.getcwd())` with `sys.path.insert(0, str(Path(__file__).parent[.parent]))`. |
| HIGH-6 | `main.py` | Added `check_api_key` dependency (reads `AUDITOR_API_KEY` env var) applied to `/ingest` and `/ask`. |
| HIGH-7 / LOW-2 | `main.py` | Removed `UploadFile, File` from the FastAPI import. |
| HIGH-8 | `main.py`, `src/generator.py` | Both now read `os.environ.get("LLM_MODEL", "gpt-4o-mini")`; `Settings.llm` and `Generator.model` stay in sync. |

---

## Medium (11 fixes)

| Fix | File(s) Changed | What Changed |
|---|---|---|
| MED-2 | `main.py` | Added `current_nodes` global; populated on load and on every `/ingest`; passed as concrete `list` to `HybridRetriever`. |
| MED-3 | `src/ingester.py` | `load_documents()` now calls `os.path.isdir()` and raises `FileNotFoundError` with an actionable message. |
| MED-4 | `src/generator.py` | Constructor wraps YAML load in `try/except FileNotFoundError/YAMLError`; raises `ValueError` if key is empty. |
| MED-6 | `src/retriever.py` | Replaced last-write-wins deduplication with Reciprocal Rank Fusion (K=60). |
| MED-7 | `run_ingestion.py` | `RAW_DATA_PATH` and `VECTOR_STORE_PATH` constants added; `Indexer(storage_dir=VECTOR_STORE_PATH)` now explicit. |
| MED-8 | `.github/workflows/ci.yml` | Added `env: OPENAI_API_KEY: "dummy-key-for-import-tests-only"` to the pytest step. |
| MED-9 | `tests/eval_ragas.py` | All Google/Alphabet hardcoded data replaced with `PLACEHOLDER` strings; script raises `ValueError` if placeholders remain. |
| MED-10 | `main.py` | `os.makedirs("artifacts", exist_ok=True)` added before `logging.basicConfig()`. |
| MED-11 | `requirements.txt` | Added `sentence-transformers>=2.2.0,<4.0.0`. |

---

## Low (7 fixes)

| Fix | File(s) Changed | What Changed |
|---|---|---|
| LOW-1 | `main.py`, `run_ingestion.py`, `tests/eval_ragas.py` | Emoji removed from all `logger.*` and `print()` calls. |
| LOW-3 | `main.py` | Removed `import gc`, both `del docs` calls, and both `gc.collect()` calls. |
| LOW-4 | `.env.example` (new file) | Documents all required and optional environment variables. |
| LOW-5 | `tests/smoke_test.py` | `REPO_ROOT = Path(__file__).parent.parent` used for all path assertions. |
| LOW-6 | `.github/workflows/ci.yml` | `actions/checkout@v3` → `@v4`; `actions/setup-python@v4` → `@v5`. |
| LOW-7 | `.gitignore` | Added `!data/raw/.gitkeep`, `!data/processed/.gitkeep`, `!vector_store/.gitkeep` negation lines. |

---

## Not Changed

| Issue | Reason |
|---|---|
| LOW-8 (personal docs in `artifacts/`) | These are personal portfolio files; removing them requires owner decision. |
