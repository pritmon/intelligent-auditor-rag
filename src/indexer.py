import os
from typing import List
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage

# The Indexer class handles creating and saving the search index
class Indexer:
    def __init__(self, storage_dir: str = "vector_store"):
        """
        Initializes the Indexer.
        
        :param storage_dir: Folder where the index files will be saved.
        """
        self.storage_dir = storage_dir
        
    def create_index(self, nodes):
        """
        Creates a new search index from the text chunks (nodes).
        """
        print("--- Creating Search Index ---")
        # Using LlamaIndex default SimpleVectorStore which is very memory efficient for small data
        index = VectorStoreIndex(nodes)

        # Persist the index; if disk I/O fails the in-memory index is still returned
        # so the current request succeeds (subsequent restarts won't reload the index).
        try:
            index.storage_context.persist(persist_dir=self.storage_dir)
            print(f"Index saved to {self.storage_dir}")
        except OSError as e:
            print(f"Warning: could not persist index to {self.storage_dir!r}: {e}. Index is in-memory only.")
        return index

    def load_index(self):
        """
        Loads an existing index from the storage folder.
        """
        # Ignore hidden files like .gitkeep
        if not os.path.exists(self.storage_dir):
            return None
            
        valid_files = [f for f in os.listdir(self.storage_dir) if not f.startswith(".")]
        if not valid_files:
            print("No existing index found. You need to create one first.")
            return None
            
        print(f"--- Loading Index from {self.storage_dir} ---")
        # Re-initialize the storage context
        storage_context = StorageContext.from_defaults(persist_dir=self.storage_dir)
        # Load the index
        index = load_index_from_storage(storage_context=storage_context)
        return index

if __name__ == "__main__":
    # Example usage (would require nodes/chunks from ingester)
    indexer = Indexer()
    print("Indexer class ready. Use it in conjunction with Ingester nodes.")
