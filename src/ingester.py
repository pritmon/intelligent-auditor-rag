import os
from typing import List
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core.node_parser import SentenceSplitter


class Ingester:
    def __init__(self, input_dir: str, chunk_size: int = 1024, chunk_overlap: int = 200):
        self.input_dir = input_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.node_parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def load_documents(self) -> List[Document]:
        # MED-3: fail fast with a clear message instead of a confusing internal error
        if not os.path.isdir(self.input_dir):
            raise FileNotFoundError(
                f"Input directory not found: {self.input_dir!r}. "
                "Create it and add PDF files before running ingestion."
            )
        reader = SimpleDirectoryReader(input_dir=self.input_dir)
        return reader.load_data()

    def create_chunks(self, documents: List[Document]):
        return self.node_parser.get_nodes_from_documents(documents)


if __name__ == "__main__":
    RAW_DATA_PATH = "data/raw"
    if not os.path.exists(RAW_DATA_PATH):
        os.makedirs(RAW_DATA_PATH)
        print(f"Created {RAW_DATA_PATH} directory. Please add some PDFs there.")
    ingester = Ingester(input_dir=RAW_DATA_PATH)
    docs = ingester.load_documents()
    if docs:
        chunks = ingester.create_chunks(docs)
        print(f"Example chunk content: {chunks[0].text[:200]}...")
    else:
        print("No documents found to process.")
