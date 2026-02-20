# Intelligent Auditor RAG Tasks

- [x] Initialize project structure
    - [x] Create directories `[x]`
    - [x] Create basic config files (`requirements.txt`, `.env`, `.gitignore`) `[x]`
- [x] Implement Core Components
    - [x] `prompts/system_prompt.yaml`
    - [x] `src/ingester.py` (Loading & Chunking)
    - [x] `src/indexer.py` (Vector Store)
    - [x] `src/retriever.py` (Hybrid Search)
    - [x] `src/reranker.py` (Ranking)
    - [x] `src/generator.py` (LLM Logic)
- [x] Implement Entry Point
    - [x] `main.py` (FastAPI implementation)
- [x] Verification
    - [x] Run basic ingestion test
    - [x] Run basic query test
