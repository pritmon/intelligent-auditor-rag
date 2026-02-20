import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

def test_imports():
    """Verify that all core components can be imported."""
    from src.ingester import Ingester # noqa
    from src.indexer import Indexer # noqa
    from src.retriever import HybridRetriever # noqa
    from src.reranker import Reranker # noqa
    from src.generator import Generator # noqa
    assert True

def test_directory_structure():
    """Verify that all required directories exist."""
    dirs = ["data/raw", "data/processed", "vector_store", "src", "prompts", "tests"]
    for d in dirs:
        assert os.path.isdir(d), f"Directory {d}/ is missing"

def test_prompt_file():
    """Verify that the system prompt file exists."""
    assert os.path.exists("prompts/system_prompt.yaml"), "prompts/system_prompt.yaml is missing"
