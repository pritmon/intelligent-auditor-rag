from llama_index.core.postprocessor import LLMRerank
from llama_index.core.schema import QueryBundle
from typing import List
import logging

logger = logging.getLogger(__name__)


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
        try:
            # MED-1: call the reranker instead of silently returning a plain slice
            return self.reranker.postprocess_nodes(
                nodes, query_bundle=QueryBundle(query_str=query)
            )
        except Exception as e:
            # LLMRerank makes internal LLM calls; if the LLM is unavailable fall back
            # to the top-N candidates by retrieval score so the endpoint still responds.
            logger.warning(
                f"LLM reranking failed ({e}); falling back to top-{self.top_n} by retrieval score."
            )
            return nodes[: self.top_n]


if __name__ == "__main__":
    print("Reranker class ready.")
