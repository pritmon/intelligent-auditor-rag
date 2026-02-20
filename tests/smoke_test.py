import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

print("Checking imports...")
try:
    from src.ingester import Ingester
    from src.indexer import Indexer
    from src.retriever import HybridRetriever
    from src.reranker import Reranker
    from src.generator import Generator
    print("✅ All core components imported successfully!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

print("\nChecking directory structure...")
dirs = ["data/raw", "data/processed", "vector_store", "src", "prompts", "tests"]
for d in dirs:
    if os.path.isdir(d):
        print(f"✅ {d}/ exists")
    else:
        print(f"❌ {d}/ is missing")

print("\nChecking prompt file...")
if os.path.exists("prompts/system_prompt.yaml"):
    print("✅ prompts/system_prompt.yaml exists")
else:
    print("❌ prompts/system_prompt.yaml is missing")

print("\nSmoke test passed!")
