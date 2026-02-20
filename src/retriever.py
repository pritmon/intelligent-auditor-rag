from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core import QueryBundle
import os

# The Retriever class handles finding the most relevant chunks of text for a question
class HybridRetriever:
    def __init__(self, index, nodes, similarity_top_k: int = 5):
        """
        Initializes the Hybrid Retriever.
        
        :param index: The vector index we created.
        :param nodes: The original text chunks (needed for BM25 keyword search).
        :param similarity_top_k: How many top results to retrieve.
        """
        # 1. Vector Search: Finds text based on "meaning"
        self.vector_retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=similarity_top_k,
        )
        
        # 2. BM25 Search: Finds text based on "exact keywords" (great for Section 404, etc.)
        self.bm25_retriever = BM25Retriever.from_defaults(
            nodes=nodes,
            similarity_top_k=similarity_top_k,
        )

    def retrieve(self, query: str):
        """
        Performs hybrid retrieval: combines meaning-based and keyword-based results.
        """
        print(f"--- Retrieving relevant context for: '{query}' ---")
        
        # Get results from both methods
        vector_results = self.vector_retriever.retrieve(query)
        bm25_results = self.bm25_retriever.retrieve(query)
        
        # Combine them (simple fusion for now)
        # Note: In a production app, we would use RRF (Reciprocal Rank Fusion) here
        all_results = vector_results + bm25_results
        
        # Remove duplicates (if any chunk was found by both)
        unique_results = {}
        for res in all_results:
            unique_results[res.node.node_id] = res
            
        print(f"Found {len(unique_results)} relevant chunks.")
        return list(unique_results.values())

if __name__ == "__main__":
    print("Retriever class ready. Use it with an Index and Nodes.")
