import sys
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# HIGH-5 / LOW-5: anchor to repo root regardless of working directory or CWD
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


def test_imports():
    """Verify that all core components can be imported."""
    from src.ingester import Ingester  # noqa: F401
    from src.indexer import Indexer  # noqa: F401
    from src.retriever import HybridRetriever  # noqa: F401
    from src.reranker import Reranker  # noqa: F401
    from src.generator import Generator  # noqa: F401
    assert True


def test_directory_structure():
    """Verify that all required directories exist (passes on a clean git clone)."""
    dirs = ["data/raw", "data/processed", "vector_store", "src", "prompts", "tests"]
    for d in dirs:
        assert (REPO_ROOT / d).is_dir(), f"Directory {d}/ is missing"


def test_prompt_file():
    """Verify that the system prompt YAML file exists."""
    assert (REPO_ROOT / "prompts/system_prompt.yaml").exists(), \
        "prompts/system_prompt.yaml is missing"


# ── Failure-handling tests ────────────────────────────────────────────────────

def test_ingester_missing_directory():
    """Ingester raises FileNotFoundError for a non-existent input directory."""
    from src.ingester import Ingester
    ingester = Ingester(input_dir="/nonexistent/path/that/does/not/exist")
    with pytest.raises(FileNotFoundError, match="Input directory not found"):
        ingester.load_documents()


def test_generator_missing_api_key(monkeypatch):
    """Generator raises RuntimeError when OPENAI_API_KEY is absent."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from src.generator import Generator
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
        Generator()


def test_generator_missing_prompt_file(monkeypatch):
    """Generator raises FileNotFoundError for a missing prompt file."""
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")
    from src.generator import Generator
    with pytest.raises(FileNotFoundError, match="System prompt file not found"):
        Generator(prompt_path="/nonexistent/prompt.yaml")


def test_reranker_empty_nodes():
    """Reranker returns an empty list immediately when given no nodes."""
    from src.reranker import Reranker
    reranker = Reranker(top_n=3)
    result = reranker.rerank("any query", [])
    assert result == []


def test_reranker_llm_failure_falls_back():
    """Reranker falls back to top-N slice when the LLM call raises an exception."""
    from src.reranker import Reranker
    reranker = Reranker(top_n=2)
    nodes = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
    with patch.object(reranker.reranker, "postprocess_nodes", side_effect=RuntimeError("LLM down")):
        result = reranker.rerank("query", nodes)
    assert result == nodes[:2]


def test_hybrid_retriever_both_fail():
    """HybridRetriever returns an empty list when both sub-retrievers raise exceptions."""
    from src.retriever import HybridRetriever
    retriever = HybridRetriever.__new__(HybridRetriever)
    retriever.vector_retriever = MagicMock()
    retriever.bm25_retriever = MagicMock()
    retriever.vector_retriever.retrieve.side_effect = RuntimeError("vector down")
    retriever.bm25_retriever.retrieve.side_effect = RuntimeError("bm25 down")
    result = retriever.retrieve("query")
    assert result == []


def test_hybrid_retriever_one_fails():
    """HybridRetriever still returns results when one sub-retriever raises an exception."""
    from src.retriever import HybridRetriever
    retriever = HybridRetriever.__new__(HybridRetriever)
    mock_node = MagicMock()
    mock_node.node.node_id = "node-1"
    retriever.vector_retriever = MagicMock()
    retriever.bm25_retriever = MagicMock()
    retriever.vector_retriever.retrieve.side_effect = RuntimeError("vector down")
    retriever.bm25_retriever.retrieve.return_value = [mock_node]
    result = retriever.retrieve("query")
    assert len(result) == 1


def test_indexer_persist_failure_returns_index(tmp_path):
    """Indexer.create_index returns a valid index even when persist raises OSError."""
    from src.indexer import Indexer
    indexer = Indexer(storage_dir=str(tmp_path / "store"))
    mock_index = MagicMock()
    mock_index.storage_context.persist.side_effect = OSError("disk full")
    with patch("src.indexer.VectorStoreIndex", return_value=mock_index):
        result = indexer.create_index([])
    assert result is mock_index


def test_generator_empty_choices_raises(monkeypatch):
    """Generator raises RuntimeError when OpenAI returns an empty choices list."""
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")
    from src.generator import Generator
    gen = Generator.__new__(Generator)
    gen.model = "gpt-4o-mini"
    gen.system_prompt_template = "Context: {context_str}\nQuestion: {query_str}"
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = []
    mock_client.chat.completions.create.return_value = mock_response
    gen.client = mock_client
    with pytest.raises(RuntimeError, match="empty choices list"):
        gen.generate_response("test query", [])
