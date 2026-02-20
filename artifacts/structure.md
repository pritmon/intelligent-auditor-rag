# Project Structure: Intelligent Auditor RAG

Below is the directory structure for the "Intelligent Auditor" project. This layout follows MLOps best practices by separating data, source code, prompts, and tests.

```text
intelligent-auditor-rag/
├── data/                   # Physical storage
│   ├── raw/                # Original PDFs (e.g., Google_10K.pdf)
│   └── processed/          # JSON/Text exports from Unstructured/LlamaParse
├── vector_store/           # Local FAISS or ChromaDB index files
├── src/                    # Source code (The "Engine")
│   ├── __init__.py
│   ├── ingester.py         # Chunking & Embedding logic
│   ├── indexer.py          # HNSW & Vector DB configuration
│   ├── retriever.py        # Hybrid Search (BM25 + Vector) & RRF
│   ├── reranker.py         # Cross-Encoder logic
│   └── generator.py        # LLM Prompting & Streaming logic
├── prompts/                # Prompt Management
│   └── system_prompt.yaml  # System instructions stored as config
├── tests/                  # Quality Assurance
│   ├── test_retrieval.py   # Unit tests for search accuracy
│   └── eval_ragas.py       # RAGAS evaluation scripts
├── .env                    # API Keys (OpenAI, LangSmith, etc.)
├── .gitignore              # Hide venv, .env, and large data files
├── requirements.txt        # Dependencies
└── main.py                 # Entry point (FastAPI or CLI)
```

## Component Descriptions

- **data/**: Contains the input documents (`raw`) and any cleaned or parsed versions (`processed`).
- **vector_store/**: Stores the generated embeddings and search indices (e.g., FAISS).
- **src/**: The modular engine of the application.
- **prompts/**: Centralized management for AI instructions, decoupled from the code.
- **tests/**: Scripts to ensure the search and generation quality remains high.
- **main.py**: The FastAPI server that ties everything together.
