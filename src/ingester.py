import os
from typing import List
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core.node_parser import SentenceSplitter

# The Ingester class handles loading files from a folder and breaking them into pieces (chunks)
class Ingester:
    def __init__(self, input_dir: str, chunk_size: int = 1024, chunk_overlap: int = 200):
        """
        Initializes the Ingester.
        
        :param input_dir: The folder where your raw PDFs are stored.
        :param chunk_size: How many characters should be in each piece of text.
        :param chunk_overlap: How many characters should overlap between pieces (to keep context).
        """
        self.input_dir = input_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # SentenceSplitter helps us break long documents into smaller, readable chunks
        self.node_parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def load_documents(self) -> List[Document]:
        """
        Loads all PDF files from the input directory.
        """
        print(f"--- Loading documents from {self.input_dir} ---")
        # SimpleDirectoryReader automatically looks for files in the folder
        reader = SimpleDirectoryReader(input_dir=self.input_dir)
        documents = reader.load_data()
        print(f"Loaded {len(documents)} document pages.")
        return documents

    def create_chunks(self, documents: List[Document]):
        """
        Takes the loaded documents and splits them into smaller 'nodes' (chunks).
        """
        print("--- Splitting documents into chunks ---")
        nodes = self.node_parser.get_nodes_from_documents(documents)
        print(f"Created {len(nodes)} chunks.")
        return nodes

if __name__ == "__main__":
    # This part only runs if you execute this file directly
    # Usage example:
    RAW_DATA_PATH = "data/raw"
    
    # Make sure the directory exists
    if not os.path.exists(RAW_DATA_PATH):
        os.makedirs(RAW_DATA_PATH)
        print(f"Created {RAW_DATA_PATH} directory. Please add some PDFs there!")
    
    ingester = Ingester(input_dir=RAW_DATA_PATH)
    docs = ingester.load_documents()
    if docs:
        chunks = ingester.create_chunks(docs)
        print(f"Example chunk content: {chunks[0].text[:200]}...")
    else:
        print("No documents found to process.")
