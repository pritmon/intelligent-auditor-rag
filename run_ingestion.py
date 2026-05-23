import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# HIGH-5: anchor to the file's own location, not the CWD
sys.path.insert(0, str(Path(__file__).parent))

from src.ingester import Ingester
from src.indexer import Indexer

# MED-7: use the same path constants as main.py
RAW_DATA_PATH = "data/raw"
VECTOR_STORE_PATH = "vector_store"


def main():
    load_dotenv()
    key = os.environ.get("OPENAI_API_KEY")

    if not key or "your_openai_api_key" in key:
        print("ERROR: OpenAI API Key not found in .env file!")
        print("Open the .env file and replace the placeholder with your real key.")
        return

    print("Starting ingestion process...")

    ingester = Ingester(input_dir=RAW_DATA_PATH)
    docs = ingester.load_documents()
    if not docs:
        print("No PDFs found in data/raw!")
        return

    chunks = ingester.create_chunks(docs)

    print("Sending chunks to OpenAI to generate embeddings...")
    indexer = Indexer(storage_dir=VECTOR_STORE_PATH)
    indexer.create_index(chunks)

    print("\nSUCCESS! Your auditor has finished reading the documents.")
    print(f"Knowledge stored in '{VECTOR_STORE_PATH}'.")
    print("\nYou can now run 'python3 main.py' to start the server and ask questions.")


if __name__ == "__main__":
    main()
