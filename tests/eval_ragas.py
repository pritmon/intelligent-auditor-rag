import os
import json
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevance, context_precision
from datasets import Dataset
from dotenv import load_dotenv

# MED-9: template evaluation dataset with generic placeholders.
# Replace each entry with real Q&A pairs sampled from your actual ingested corpus.
# Running /ingest first and then manually verifying a handful of answers is the
# recommended way to build a meaningful evaluation set.
EVAL_DATA_TEMPLATE = {
    "question": [
        "What is the total revenue reported for the period?",
        "What are the primary risk factors disclosed?",
        "What is the net income for the most recent fiscal year?",
    ],
    "answer": [
        # Replace with answers produced by your RAG pipeline
        "PLACEHOLDER: answer from /ask endpoint",
        "PLACEHOLDER: answer from /ask endpoint",
        "PLACEHOLDER: answer from /ask endpoint",
    ],
    "contexts": [
        # Replace with the actual retrieved chunks returned by your retriever
        ["PLACEHOLDER: retrieved context chunk(s)"],
        ["PLACEHOLDER: retrieved context chunk(s)"],
        ["PLACEHOLDER: retrieved context chunk(s)"],
    ],
    "ground_truth": [
        # Replace with the correct answers from the source document
        "PLACEHOLDER: verified ground-truth answer",
        "PLACEHOLDER: verified ground-truth answer",
        "PLACEHOLDER: verified ground-truth answer",
    ],
}


def run_evaluation(data: dict = None):
    load_dotenv()

    if data is None:
        data = EVAL_DATA_TEMPLATE

    # Guard against accidentally running with placeholder data
    if any("PLACEHOLDER" in v for v in data.get("answer", [])):
        raise ValueError(
            "Evaluation dataset still contains placeholder values. "
            "Replace them with real Q&A pairs derived from your ingested documents."
        )

    dataset = Dataset.from_dict(data)
    print("Evaluating RAG pipeline accuracy...")

    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevance,
            context_precision,
        ],
    )

    print("\nEvaluation results:")
    print(result)

    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/evaluation_report.json", "w") as f:
        json.dump(result, f, indent=4)
    print("\nReport saved to artifacts/evaluation_report.json")
    return result


if __name__ == "__main__":
    try:
        run_evaluation()
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Evaluation failed: {e}")
        print("Tip: make sure OPENAI_API_KEY is set and 'ragas' and 'datasets' are installed.")
