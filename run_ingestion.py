import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

from src.ingester import Ingester
from src.indexer import Indexer

def main():
    # 1. Load environment variables
    load_dotenv()
    key = os.environ.get("OPENAI_API_KEY")
    
    if not key or "your_openai_api_key" in key:
        print("❌ ERROR: OpenAI API Key not found in .env file!")
        print("Please open the .env file and replace 'your_openai_api_key_here' with your real key.")
        return

    print("🚀 Starting Ingestion Process...")
    
    # 2. Setup Ingester
    RAW_DATA_PATH = "data/raw"
    ingester = Ingester(input_dir=RAW_DATA_PATH)
    
    # 3. Load and Chunk
    docs = ingester.load_documents()
    if not docs:
        print("❌ No PDFs found in data/raw!")
        return
        
    chunks = ingester.create_chunks(docs)
    
    # 4. Create Index (This will call OpenAI to generate 'meanings/embeddings')
    print("🧠 The system is now sending chunks to OpenAI to understand their meaning...")
    print("(This step requires a valid API Key and may take a moment per file)")
    
    indexer = Indexer()
    indexer.create_index(chunks)
    
    print("\n✅ SUCCESS! Your auditor has finished reading the documents.")
    print("The knowledge is now stored in the 'vector_store' folder.")
    print("\nYou can now run 'python3 main.py' to start the server and ask questions!")

if __name__ == "__main__":
    main()
