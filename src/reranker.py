from llama_index.core.postprocessor import LLMRerank
from llama_index.core.schema import QueryBundle
from typing import List


class Reranker:
    def __init__(self, top_n: int = 3):
        """
        Reranks retrieved chunks using the LLM configured in Settings.llm.

        Note: LLMRerank makes additional LLM calls (one per choice_batch_size nodes).
        For a cheaper alternative, swap in SentenceTransformerRerank from
        llama-index-postprocessor-sentence-transformer-rerank which runs locally.
        """
        self.top_n = top_n
        # MED-1: actually used in rerank() below — previously was never called
        self.reranker = LLMRerank(choice_batch_size=5, top_n=top_n)

    def rerank(self, query: str, nodes: List) -> List:
        """Rerank retrieved nodes using LLM-based relevance scoring."""
        if not nodes:
            return nodes
        # MED-1: call the reranker instead of silently returning a plain slice
        return self.reranker.postprocess_nodes(
            nodes, query_bundle=QueryBundle(query_str=query)
        )


if __name__ == "__main__":
    print("Reranker class ready.")
