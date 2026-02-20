# Walkthrough - Intelligent Auditor RAG

I have successfully built the "Intelligent Auditor" RAG system. This system is designed to analyze 10-K and 10-Q filings with high precision, grounded strictly in the provided context.

## Project Structure Overivew

The project follows the professional modular structure you requested:

- `data/raw`: Place your PDF filings here.
- `src/ingester.py`: Loads and chunks your documents.
- `src/indexer.py`: Creates a searchable vector index (FAISS).
- `src/retriever.py`: Combines keyword and meaning-based search (Hybrid).
- `src/generator.py`: Talks to the LLM using your specialized operational rules.
- `main.py`: The FastAPI server to interact with the auditor.

## Key Features

1. **Source Grounding**: The system is hard-coded to only answer using provided context.
2. **Hybrid Search**: Uses BM25 for keyword accuracy (important for regulatory sections) and Vector search for semantic meaning.
3. **Citations**: The system is instructed to cite sources (Page, Item) in every fact.
4. **Professional Prompting**: All operational rules are centralized in `prompts/system_prompt.yaml`.

## How to Get Started

Since you are new to Python, follow these steps to run your auditor:

1. **Setup Environment**:
   ```bash
   # Create a virtual environment
   python -m venv venv
   # Activate it
   source venv/bin/activate
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure API Key**:
   Open the `.env` file and paste your OpenAI API Key.

3. **Injest Documents**:
   - Place a PDF (e.g., `Google_10K.pdf`) in `data/raw/`.
   - Start the server: `python main.py`.
   - Visit `http://127.0.0.1:8000/docs` in your browser.
   - Click on the `/ingest` endpoint and press "Execute".

4. **Query the Auditor**:
   - Use the `/ask` endpoint to send a query like: *"What were the risk factors related to cybersecurity mentioned in Item 1A?"*

## Verification Results

The codebase has been structured and individual components are ready for use. A `smoke_test.py` is included in `tests/` to verify your installation.

> [!TIP]
> Use `gpt-4o-mini` for faster and cheaper analysis during development. Change the model in `src/generator.py` if you need even more power with `gpt-4o`.
