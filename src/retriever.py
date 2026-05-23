from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from typing import List


class HybridRetriever:
    def __init__(self, index, nodes, similarity_top_k: int = 5):
        """
        Hybrid retriever combining dense vector search and sparse BM25 keyword search.

        :param index: The VectorStoreIndex built by Indexer.
        :param nodes: Concrete list of TextNode objects for BM25 (not dict_values).
        :param similarity_top_k: Candidate pool size from each retriever before fusion.
        """
        self.vector_retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=similarity_top_k,
        )
        # MED-2: ensure a concrete list so BM25Retriever receives the right type
        self.bm25_retriever = BM25Retriever.from_defaults(
            nodes=list(nodes),
            similarity_top_k=similarity_top_k,
        )

    def retrieve(self, query: str) -> List:
        """
        Retrieve via both methods and fuse results using Reciprocal Rank Fusion (RRF).

        RRF assigns each document a score of sum(1 / (K + rank)) across all ranked
        lists, giving high combined scores to documents that appear near the top in
        multiple lists without requiring score normalisation.
        """
        vector_results = self.vector_retriever.retrieve(query)
        bm25_results = self.bm25_retriever.retrieve(query)

        # MED-6: Reciprocal Rank Fusion — preserves signal from both retrievers
        K = 60  # standard RRF constant; higher K reduces the impact of rank differences
        rrf_scores: dict = {}
        rrf_nodes: dict = {}

        for rank, result in enumerate(vector_results):
            nid = result.node.node_id
            rrf_scores[nid] = rrf_scores.get(nid, 0.0) + 1.0 / (K + rank + 1)
            rrf_nodes[nid] = result

        for rank, result in enumerate(bm25_results):
            nid = result.node.node_id
            rrf_scores[nid] = rrf_scores.get(nid, 0.0) + 1.0 / (K + rank + 1)
            # Keep the vector result when a node appears in both (higher-quality score)
            if nid not in rrf_nodes:
                rrf_nodes[nid] = result

        sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)
        return [rrf_nodes[nid] for nid in sorted_ids]


if __name__ == "__main__":
    print("Retriever class ready. Use it with an Index and Nodes.")
