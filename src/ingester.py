import os
import logging
from typing import List
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core.node_parser import SentenceSplitter

logger = logging.getLogger(__name__)


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
        # Try loading all files at once; if the batch fails (e.g. one corrupt PDF
        # causes SimpleDirectoryReader to abort) fall back to per-file loading so
        # that valid documents are still indexed.
        try:
            reader = SimpleDirectoryReader(input_dir=self.input_dir)
            return reader.load_data()
        except Exception as batch_err:
            logger.warning(f"Batch load failed ({batch_err}); retrying file-by-file.")
            return self._load_files_individually()

    def _load_files_individually(self) -> List[Document]:
        """Load each file separately, skipping files that cannot be parsed."""
        docs: List[Document] = []
        for fname in sorted(os.listdir(self.input_dir)):
            fpath = os.path.join(self.input_dir, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                file_reader = SimpleDirectoryReader(input_files=[fpath])
                docs.extend(file_reader.load_data())
                logger.info(f"Loaded {fname!r}")
            except Exception as e:
                logger.warning(f"Skipping {fname!r}: could not parse ({e})")
        if not docs:
            raise RuntimeError(
                f"No documents could be loaded from {self.input_dir!r}. "
                "Check that the directory contains valid PDF files."
            )
        return docs

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
