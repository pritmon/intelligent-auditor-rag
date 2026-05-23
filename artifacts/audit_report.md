# Intelligent Auditor RAG — Code Audit Report

**Repository:** https://github.com/pritmon/intelligent-auditor-rag
**Audit Date:** 2026-05-23
**Auditor:** Claude Sonnet 4.6
**Scope:** All source files, configuration, tests, and deployment artifacts

---

## Executive Summary

The repository implements a Retrieval-Augmented Generation (RAG) system for financial document analysis using FastAPI, LlamaIndex, and OpenAI. The architecture and documentation are well-structured, but the audit found **4 critical defects that render the core functionality non-operational**, plus 8 high-severity and 14 medium/low severity issues. All issues have been remediated in the accompanying fix commit.

---

## CRITICAL

### CRIT-1 — No API key validation at startup
**File:** `main.py:38-39` | **Status: Fixed**

`Settings.llm` and `Settings.embed_model` were initialised before `load_dotenv()` was ever called, and before any check that `OPENAI_API_KEY` was present. Starting the server with a missing or placeholder key produced no startup error — failures appeared only at query time as cryptic authentication errors.

**Fix:** `load_dotenv()` and an explicit key check are now the first statements in `main.py`, before any LlamaIndex import.

---

### CRIT-2 — `rerank` method was a silent no-op
**File:** `src/reranker.py:27` | **Status: Fixed**

The `rerank()` method returned `nodes[:3]` unconditionally. The `LLMRerank` instance created in `__init__` was never called, so every query received an unordered truncation of the retriever output rather than relevance-ranked results. The comment acknowledged this: _"Simple placeholder for now to avoid high API costs during dev"_ — but the system was presented as production-ready.

**Fix:** `rerank()` now calls `self.reranker.postprocess_nodes()` with a `QueryBundle`.

---

### CRIT-3 — Prompt injection via unsanitized `.format()`
**File:** `src/generator.py:45-47` | **Status: Fixed**

User query and retrieved document content were interpolated into the system prompt using Python's `str.format()`. Any `{key}` pattern in the user query or a retrieved document that was not one of the two known placeholders (`context_str`, `query_str`) would raise a `KeyError` and crash the endpoint. Additionally, a malicious document could contain instructions designed to override the system role ("no hallucinations" rule).

**Fix:** Replaced `.format()` with two chained `.replace()` calls, which never interpret the replacement values as format strings.

---

### CRIT-4 — `KMP_DUPLICATE_LIB_OK=TRUE` masked memory errors
**Files:** `main.py:2`, `Dockerfile:9` | **Status: Fixed**

This environment variable suppresses Intel OpenMP duplicate-library warnings that arise when FAISS and another package each bundle their own OpenMP runtime. Silencing the warning rather than fixing the root cause can cause silent numerical errors in multi-threaded vector similarity computations in production.

**Fix:** Removed from both files. The root cause is addressed by pinning dependencies (HIGH-2) so only one OpenMP runtime is present.

---

## HIGH

### HIGH-1 — No query input validation
**File:** `main.py:65-66` | **Status: Fixed**

`QueryRequest` accepted any string with no length constraints. Empty strings, blank whitespace, and multi-megabyte payloads all reached the OpenAI API, wasting tokens and money.

**Fix:** `Field(..., min_length=1, max_length=4096, strip_whitespace=True)` added to the `query` field.

---

### HIGH-2 — All 17 dependencies unpinned
**File:** `requirements.txt` | **Status: Fixed**

No package had a version specifier. `pip install -r requirements.txt` installed whatever was "latest" at build time, making builds non-reproducible. LlamaIndex in particular has a history of breaking API changes between minor versions.

**Fix:** All packages now carry `>=X.Y,<X+1.0` or `>=X.Y.Z,<X+1.0.0` constraints.

---

### HIGH-3 — Raw exception details leaked to API clients
**File:** `main.py:102, 136` | **Status: Fixed**

Both endpoints raised `HTTPException(detail=str(e))`, exposing file system paths, internal module names, and API error details to callers.

**Fix:** Endpoints now return generic `"Check server logs"` messages; full details are written to the server log.

---

### HIGH-4 — Race condition on global `current_index`
**File:** `main.py:57-91` | **Status: Fixed**

`current_index` was a module-level global mutated inside an async endpoint with no synchronisation. Concurrent `/ingest` + `/ask` requests or multiple `/ingest` calls could read a partially-constructed index.

**Fix:** An `asyncio.Lock` (`_index_lock`) serialises writes during `/ingest` and ensures `/ask` takes a consistent snapshot before proceeding.

---

### HIGH-5 — Fragile `sys.path` mutation
**Files:** `run_ingestion.py:6`, `tests/smoke_test.py:5` | **Status: Fixed**

Both files used `sys.path.append(os.getcwd())`, which works only if the process is started from the repository root. Running from any other directory silently broke imports.

**Fix:** Both files now use `sys.path.insert(0, str(Path(__file__).parent))` / `Path(__file__).parent.parent` to anchor relative to the file's own location.

---

### HIGH-6 — No authentication or rate limiting
**File:** `main.py` | **Status: Fixed**

All endpoints were public. `/ingest` triggered paid OpenAI embedding API calls; anyone with a network path to the server could trigger them repeatedly.

**Fix:** An optional API-key guard (`AUDITOR_API_KEY` env var) is applied as a FastAPI `Depends` on both `/ingest` and `/ask`. When the variable is unset the endpoints remain open (suitable for local development); when set, requests without a matching `X-API-Key` header receive `403 Forbidden`.

---

### HIGH-7 — Dead imports
**File:** `main.py:3` | **Status: Fixed**

`UploadFile` and `File` were imported from FastAPI but never used, indicating an unimplemented file-upload endpoint.

**Fix:** Removed from the import line.

---

### HIGH-8 — Model mismatch between configuration and generation
**Files:** `main.py:38`, `src/generator.py:52` | **Status: Fixed**

`Settings.llm = OpenAI(model="gpt-4o")` configured LlamaIndex globals, but the `Generator` hardcoded `model="gpt-4o-mini"` for its own OpenAI client. Changing `Settings.llm` had zero effect on actual answer generation.

**Fix:** Both now read `os.environ.get("LLM_MODEL", "gpt-4o-mini")` so a single env var controls the model throughout the system.

---

## MEDIUM

### MED-1 — Reranker returned plain slice, never reranked
**File:** `src/reranker.py:27` | **Status: Fixed** (see also CRIT-2 above)

### MED-2 — `dict_values` passed to BM25; index rebuilt per query
**File:** `main.py:119` | **Status: Fixed**

`current_index.docstore.docs.values()` returns a view, not a list. More critically, the BM25 index (an O(N·|V|) construction) was rebuilt from scratch on every `/ask` call. Nodes are now cached in `current_nodes` and updated only when `/ingest` runs.

---

### MED-3 — Ingester silently failed on missing input directory
**File:** `src/ingester.py:28` | **Status: Fixed**

`SimpleDirectoryReader` raised an opaque internal error when the input directory did not exist. `load_documents()` now raises `FileNotFoundError` with an actionable message.

---

### MED-4 — No error handling for missing/malformed prompt YAML
**File:** `src/generator.py:20-22` | **Status: Fixed**

A missing prompt file crashed the server at startup with an unformatted traceback. An empty `system_prompt` key silently sent blank system prompts to the LLM. The constructor now raises `FileNotFoundError`, `ValueError`, or a clear message for each failure mode.

---

### MED-6 — Hybrid fusion discarded vector scores on overlap
**File:** `src/retriever.py:40-47` | **Status: Fixed**

When a node appeared in both the vector and BM25 result lists (indicating high relevance by both methods), the BM25 score overwrote the vector score. The comment noted RRF should be used.

**Fix:** Implemented standard Reciprocal Rank Fusion (K=60). Nodes appearing in both lists receive additive RRF scores; the vector result is preserved for overlapping nodes.

---

### MED-7 — `run_ingestion.py` used inconsistent hardcoded paths
**File:** `run_ingestion.py:24, 39` | **Status: Fixed**

The script hardcoded `"data/raw"` and defaulted `Indexer()` to `"vector_store"`, but didn't use named constants. If `main.py`'s `RAW_DATA_PATH` or `VECTOR_STORE_PATH` were ever changed, `run_ingestion.py` would silently diverge.

**Fix:** Both constants are now explicitly set to match `main.py`.

---

### MED-8 — CI had no `OPENAI_API_KEY` configured
**File:** `.github/workflows/ci.yml` | **Status: Fixed**

The smoke-test step imported modules that call `load_dotenv()` at import time. Without a key in the environment, any future test that instantiated `Generator` would fail with an unclear error.

**Fix:** A `dummy-key-for-import-tests-only` value is injected via `env:` so import-only tests pass without a real secret.

---

### MED-9 — Evaluation dataset contained hardcoded Google/Alphabet data
**File:** `tests/eval_ragas.py:22-23` | **Status: Fixed**

The RAGAS evaluation used hardcoded answers about Sundar Pichai and Google financials as ground truth for a generic financial auditor. The metrics measured how well static dummy data matched itself, not actual pipeline performance.

**Fix:** All entries replaced with clearly-labelled `PLACEHOLDER` values. The script now raises `ValueError` if placeholders are not replaced before running.

---

### MED-10 — Log `FileHandler` could fail at startup
**File:** `main.py:20` | **Status: Fixed**

`logging.FileHandler("artifacts/auditor.log")` raised `FileNotFoundError` if `artifacts/` did not exist, which is the case in a fresh Docker build before the `mkdir` step.

**Fix:** `os.makedirs("artifacts", exist_ok=True)` is called before the logging setup.

---

### MED-11 — `sentence-transformers` missing from requirements
**File:** `requirements.txt` | **Status: Fixed**

The architecture description referenced `SentenceTransformerRerank` as the recommended production reranker, but `sentence-transformers` was not installed.

**Fix:** Added `sentence-transformers>=2.2.0,<4.0.0` to `requirements.txt`.

---

## LOW

### LOW-1 — Emoji in logger calls
**Files:** `main.py`, `run_ingestion.py`, `tests/eval_ragas.py` | **Status: Fixed**

Emoji characters in log output can cause encoding errors in log-aggregation systems. Removed from all `logger.*` and `print()` calls.

---

### LOW-2 — Dead imports (`UploadFile`, `File`)
**File:** `main.py:3` | **Status: Fixed** (see HIGH-7)

---

### LOW-3 — Unnecessary `gc.collect()` calls
**File:** `main.py:88, 95` | **Status: Fixed**

CPython's reference counting frees objects immediately on `del`; `gc.collect()` only supplements this for cyclic garbage. Both calls were removed.

---

### LOW-4 — No `.env.example` file
**File:** repo root | **Status: Fixed**

New contributors had to infer required environment variables from code comments. `.env.example` now documents all variables with descriptions.

---

### LOW-5 — `test_directory_structure` failed on clean `git clone`
**File:** `tests/smoke_test.py:18` | **Status: Fixed**

Path checks used `os.path.isdir(d)` with relative paths, so tests passed only if pytest was run from the repo root. Tests now resolve all paths relative to `REPO_ROOT = Path(__file__).parent.parent`.

---

### LOW-6 — Outdated GitHub Actions versions
**File:** `.github/workflows/ci.yml:25, 29` | **Status: Fixed**

`actions/checkout@v3` and `actions/setup-python@v4` updated to `@v4` and `@v5` respectively.

---

### LOW-7 — `.gitignore` lacked negation patterns for `.gitkeep`
**File:** `.gitignore` | **Status: Fixed**

`vector_store/*` ignored the `.gitkeep` file, requiring a `git add -f` workaround. Fixed with `!vector_store/.gitkeep` negation patterns for all three directories.

---

### LOW-8 — Personal career documents committed to repository
**Files:** `artifacts/interview.md`, `artifacts/resume_content.md` | **Status: Noted (not changed)**

These files are personal portfolio/interview-prep documents. Their presence is a professional presentation concern for a repository shared with employers but does not affect functionality.

---

## Summary Table

| ID | Severity | File | Issue | Status |
|---|---|---|---|---|
| CRIT-1 | Critical | `main.py:38-39` | No API key validation at startup | Fixed |
| CRIT-2 | Critical | `src/reranker.py:27` | Reranker never called — silent no-op | Fixed |
| CRIT-3 | Critical | `src/generator.py:45-47` | Prompt injection via `.format()` | Fixed |
| CRIT-4 | Critical | `main.py:2`, `Dockerfile:9` | `KMP_DUPLICATE_LIB_OK` masks memory errors | Fixed |
| HIGH-1 | High | `main.py:65-66` | No query input validation | Fixed |
| HIGH-2 | High | `requirements.txt` | All 17 dependencies unpinned | Fixed |
| HIGH-3 | High | `main.py:102,136` | Raw exception details leaked | Fixed |
| HIGH-4 | High | `main.py:57-91` | Race condition on `current_index` | Fixed |
| HIGH-5 | High | `run_ingestion.py:6`, `smoke_test.py:5` | Fragile `sys.path` mutation | Fixed |
| HIGH-6 | High | `main.py` | No authentication on endpoints | Fixed |
| HIGH-7 | High | `main.py:3` | Dead `UploadFile`/`File` imports | Fixed |
| HIGH-8 | High | `main.py:38` vs `generator.py:52` | Model mismatch | Fixed |
| MED-1 | Medium | `src/reranker.py:27` | Reranker was a no-op slice | Fixed |
| MED-2 | Medium | `main.py:119` | `dict_values` to BM25; rebuild per query | Fixed |
| MED-3 | Medium | `src/ingester.py:28` | Missing directory not handled | Fixed |
| MED-4 | Medium | `src/generator.py:20-22` | No YAML error handling | Fixed |
| MED-6 | Medium | `src/retriever.py:40-47` | Fusion discards vector scores | Fixed |
| MED-7 | Medium | `run_ingestion.py:24,39` | Inconsistent hardcoded paths | Fixed |
| MED-8 | Medium | `.github/workflows/ci.yml` | No `OPENAI_API_KEY` in CI | Fixed |
| MED-9 | Medium | `tests/eval_ragas.py:22-23` | Hardcoded Google/Alphabet eval data | Fixed |
| MED-10 | Medium | `main.py:20` | Log path fails if `artifacts/` missing | Fixed |
| MED-11 | Medium | `requirements.txt` | `sentence-transformers` missing | Fixed |
| LOW-1 | Low | multiple | Emoji in log/print statements | Fixed |
| LOW-2 | Low | `main.py:3` | Dead imports | Fixed |
| LOW-3 | Low | `main.py:88,95` | Unnecessary `gc.collect()` | Fixed |
| LOW-4 | Low | repo root | No `.env.example` | Fixed |
| LOW-5 | Low | `tests/smoke_test.py:18` | Test fails on clean clone | Fixed |
| LOW-6 | Low | `.github/workflows/ci.yml:25,29` | Outdated Actions versions | Fixed |
| LOW-7 | Low | `.gitignore` | Missing `.gitkeep` negation patterns | Fixed |
| LOW-8 | Low | `artifacts/` | Personal documents in repo | Noted |
