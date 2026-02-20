import os
from typing import List
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

# The Indexer class handles creating and saving the search index
class Indexer:
    def __init__(self, storage_dir: str = "vector_store", embedding_dim: int = 1536):
        """
        Initializes the Indexer.
        
        :param storage_dir: Folder where the index files will be saved.
        :param embedding_dim: The size of the AI's internal representation (OpenAI's default is 1536).
        """
        self.storage_dir = storage_dir
        self.embedding_dim = embedding_dim
        
    def create_index(self, nodes):
        """
        Creates a new search index from the text chunks (nodes).
        """
        print("--- Creating FAISS Index ---")
        # Create a FAISS index (HNSW is a fast search algorithm)
        faiss_index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Setup the vector store
        vector_store = FaissVectorStore(faiss_index=faiss_index)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Build the index using LlamaIndex
        index = VectorStoreIndex(nodes, storage_context=storage_context)
        
        # Save the index to a folder so we don't have to rebuild it every time
        index.storage_context.persist(persist_dir=self.storage_dir)
        print(f"Index saved to {self.storage_dir}")
        return index

    def load_index(self):
        """
        Loads an existing index from the storage folder.
        """
        # Ignore hidden files like .gitkeep
        valid_files = [f for f in os.listdir(self.storage_dir) if not f.startswith(".")]
        if not os.path.exists(self.storage_dir) or not valid_files:
            print("No existing index found. You need to create one first.")
            return None
            
        # Check if essential FAISS files actually exist
        if not any(f.endswith(".faiss") or f.endswith(".json") for f in valid_files):
            print("No valid FAISS index files found. You need to create one first.")
            return None
            
        print(f"--- Loading Index from {self.storage_dir} ---")
        # Re-initialize the vector store
        vector_store = FaissVectorStore.from_persist_dir(self.storage_dir)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store, persist_dir=self.storage_dir
        )
        # Load the index
        index = load_index_from_storage(storage_context=storage_context)
        return index

if __name__ == "__main__":
    # Example usage (would require nodes/chunks from ingester)
    indexer = Indexer()
    print("Indexer class ready. Use it in conjunction with Ingester nodes.")
