import sys
import os
from pathlib import Path

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
