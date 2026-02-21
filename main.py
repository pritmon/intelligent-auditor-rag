import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import shutil
from src.ingester import Ingester
from src.indexer import Indexer
from src.retriever import HybridRetriever
from src.reranker import Reranker
from src.generator import Generator
import logging
import gc
from llama_index.core import Settings

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("artifacts/auditor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("IntelligentAuditor")

# LangSmith Observability (Optional but recommended)
# To use: Set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY in .env
if os.environ.get("LANGCHAIN_TRACING_V2") == "true":
    logger.info("🔭 LangSmith Tracing is ENABLED.")

# This is the main file that starts your "Intelligent Auditor" app.
# It uses FastAPI, which allows other apps or websites to talk to this system.

# Aggressive Memory Optimization for Free Tiers (512MB RAM)
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

Settings.llm = OpenAI(model="gpt-4o")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.chunk_size = 512  

app = FastAPI(title="Intelligent Auditor RAG")

# Initialize our components
RAW_DATA_PATH = "data/raw"
VECTOR_STORE_PATH = "vector_store"

# Helper to ensure directories exist
os.makedirs(RAW_DATA_PATH, exist_ok=True)
os.makedirs(VECTOR_STORE_PATH, exist_ok=True)

# These placeholders will hold our engine components
ingester = Ingester(input_dir=RAW_DATA_PATH)
indexer = Indexer(storage_dir=VECTOR_STORE_PATH)
generator = Generator()

# Global variable to hold the search index in memory
try:
    current_index = indexer.load_index()
except Exception as e:
    logger.warning(f"Could not load index during startup: {e}. You will need to ingest data first.")
    current_index = None

# Data structure for the questions the user will ask
class QueryRequest(BaseModel):
    query: str

@app.post("/ingest")
async def ingest_documents():
    """
    Step 1: Read the PDFs in data/raw and build the search index.
    Call this after you put new files in the folder.
    """
    global current_index
    logger.info("🚀 Starting ingestion process...")
    try:
        # 1. Load Documents
        docs = ingester.load_documents()
        if not docs:
            logger.warning("No documents found in data/raw")
            return {"message": "No documents found in data/raw"}
        
        # 2. Create Chunks
        chunks = ingester.create_chunks(docs)
        
        # 3. Clean up raw documents to save RAM
        del docs
        gc.collect()
        
        # 4. Create Index
        current_index = indexer.create_index(chunks)
        
        # 5. Final cleanup
        num_chunks = len(chunks)
        del chunks
        gc.collect()
        
        logger.info(f"✅ Successfully indexed {num_chunks} chunks.")
        return {"message": f"Successfully indexed {num_chunks} chunks."}
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_auditor(request: QueryRequest):
    """
    Step 2: Ask a question about the indexed documents.
    """
    if not current_index:
        logger.error("Query failed: Index not found.")
        raise HTTPException(status_code=400, detail="Search index not found. Please run /ingest first.")

    logger.info(f"❓ User Query: {request.query}")
    try:
        # 1. Retrieve relevant info
        # We need the original nodes for BM25 keyword search
        # Normally you'd store nodes or fetch them from the index
        # For simplicity, we'll re-fetch them or use index nodes
        retriever = HybridRetriever(index=current_index, nodes=current_index.docstore.docs.values())
        relevant_chunks = retriever.retrieve(request.query)
        
        # 2. Rerank for precision
        reranker = Reranker()
        best_chunks = reranker.rerank(request.query, relevant_chunks)
        
        # 3. Generate answer
        answer = generator.generate_response(request.query, best_chunks)
        
        logger.info("✨ Answer generated successfully.")
        return {
            "query": request.query,
            "answer": answer
        }
    except Exception as e:
        logger.error(f"❌ Error during query processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "Welcome to the Intelligent Auditor. Use /docs to see the interface."}

if __name__ == "__main__":
    import uvicorn
    # This starts the server on your computer
    print("Starting Intelligent Auditor server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
