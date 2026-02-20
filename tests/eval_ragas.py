import os
import json
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevance, context_precision
from datasets import Dataset
from dotenv import load_dotenv

# This script evaluates your RAG system's performance using RAGAS.
# It measures how accurate and honest your AI is.

def run_evaluation():
    load_dotenv()
    
    # Sample evaluation dataset (In a real scenario, you'd use a larger set of Q&A)
    data_sample = {
        "question": [
            "What is the net income of the company?",
            "Who is the CEO?",
            "What are the main risks mentioned in the report?"
        ],
        "answer": [
            "The net income was $15.3 billion as per the consolidated statement of operations.",
            "The CEO is Sundar Pichai.",
            "The main risks include competition, economic conditions, and regulatory changes."
        ],
        "contexts": [
            ["Net income was $15.3 billion. Operating expenses increased by 10%."],
            ["Sundar Pichai has served as Chief Executive Officer since 2015."],
            ["Risk Factors: We face significant competition. Economic downturns may impact revenue. Regulatory scrutiny is increasing."]
        ],
        "ground_truth": [
            "15.3 billion",
            "Sundar Pichai",
            "Competition, economy, and regulation."
        ]
    }

    dataset = Dataset.from_dict(data_sample)

    print("📊 Evaluating RAG Pipeline Accuracy...")
    
    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevance,
            context_precision,
        ],
    )

    print("\n✅ Evaluation Results:")
    print(result)
    
    # Save results to artifacts
    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/evaluation_report.json", "w") as f:
        json.dump(result, f, indent=4)
        print("\n📄 Report saved to artifacts/evaluation_report.json")

if __name__ == "__main__":
    try:
        run_evaluation()
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        print("Tip: Make sure OPENAI_API_KEY is set and you have 'ragas' and 'datasets' installed.")
