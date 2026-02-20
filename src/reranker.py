from llama_index.core.postprocessor import LLMRerank
from llama_index.core import Settings
from typing import List

# The Reranker class takes the initial search results and "double-checks" them
# to make sure the most relevant ones are at the top.
class Reranker:
    def __init__(self, top_n: int = 3):
        """
        Initializes the Reranker.
        
        :param top_n: Number of final chunks to keep after reranking.
        """
        # LLMReranker uses the LLM to decide which chunk is best suited for the query
        self.reranker = LLMRerank(choice_batch_size=5, top_n=top_n)

    def rerank(self, query: str, nodes: List):
        """
        Reranks the retrieved nodes to improve precision.
        """
        print("--- Reranking results for better precision ---")
        # In LlamaIndex, postprocessors handle things like reranking
        # This will use the LLM to score our chunks based on how well they answer the query
        # For simplicity in this local version, we'll assume the LLM is configured in Settings
        
        # Note: In a real app, you might use 'SentenceTransformerRerank' for faster performance
        return nodes[:3] # Simple placeholder for now to avoid high API costs during dev

if __name__ == "__main__":
    print("Reranker class ready.")
