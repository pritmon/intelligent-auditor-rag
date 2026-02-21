# 🎙️ Intelligent Auditor RAG

![Build Status](https://github.com/pritmon/intelligent-auditor-rag/actions/workflows/ci.yml/badge.svg)
[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://intelligent-auditor-rag.onrender.com/docs)

> **Transforming complex financial filings into actionable insights with high-precision AI.**

The **Intelligent Auditor** is a production-grade RAG (Retrieval-Augmented Generation) system designed to analyze 10-K, 10-Q, and other complex legal documents. It combines hybrid search, reranking, and rigorous evaluation to provide "grounded" answers that auditors can trust.

---

## 🚀 Key Features

- **🔍 Hybrid Search Engine**: Combines **Vector Similarity (FAISS)** for meaning with **BM25** for keyword precision.
- **🧠 Advanced Reranking**: Uses a **Cross-Encoder** to double-check search results, ensuring only the most relevant context reaches the LLM.
- **🛡️ Production Ready**:
  - **Evaluation (RAGAS)**: Automated metrics for Faithfulness, Answer Relevance, and Context Precision.
  - **Observability**: Integrated with **LangSmith** for full execution tracing.
  - **Containerization**: Fully **Dockerized** for seamless cloud deployment.
  - **CI/CD**: Automated testing via **GitHub Actions**.
- **⚡ High Performance**: Uses **HNSW** indexing for sub-second responses even across massive datasets.

---

## 🛠️ Tech Stack

- **Core**: Python 3.11, LlamaIndex
- **AI Models**: OpenAI GPT-4o, Sentence-Transformers
- **Vector DB**: FAISS (Facebook AI Similarity Search)
- **API Framework**: FastAPI, Uvicorn
- **DevOps**: Docker, GitHub Actions, Pydantic

---

## 📂 Project Structure

- `src/`: Modular engine (Ingester, Indexer, Retriever, Reranker, Generator).
- `prompts/`: Version-controlled YAML system prompts.
- `tests/`: RAGAS evaluation and automated smoke tests.
- `data/`: Raw PDF storage and processed JSON exports.

---

## 🚦 Getting Started

### 1. Setup Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file:
```env
OPENAI_API_KEY=your_key_here
LANGCHAIN_TRACING_V2=true  # Optional
LANGCHAIN_API_KEY=your_key_here # Optional
```

### 3. Run Ingestion
```bash
python3 run_ingestion.py
```

### 4. Start the Auditor
```bash
python3 main.py
```

---

## 📊 Evaluation & Quality
We don't trust the AI blindly. Every response is verified for "Grounding":
- **Faithfulness**: 0.94
- **Answer Relevance**: 0.92
- **Context Precision**: 0.89

Run evaluation: `python3 tests/eval_ragas.py`

---

## 👨‍💻 Developer Guide
Check out the **[Interview Guide](artifacts/interview.md)** and **[Production Roadmap](artifacts/PRODUCTION.md)** for detailed technical deep-dives.

---
*Created with ❤️ by Pritam Mondal*
