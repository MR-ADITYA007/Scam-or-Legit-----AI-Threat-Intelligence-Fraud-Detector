import os
import sys
import json
import time
from typing import Dict, Any, List

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from risk_engine import risk_engine
from rag_engine import rag_engine

def run_evaluation(dataset_path: str = None):
    if dataset_path is None:
        dataset_path = os.path.join(os.path.dirname(__file__), "dataset.json")

    if not os.path.exists(dataset_path):
        print(f"[ERROR] Evaluation dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print("=" * 70)
    print(f"   SCAM OR LEGIT? — SYSTEM ACCURACY EVALUATION (N={len(dataset)})")
    print("=" * 70)

    tp = 0  # True Positives (Scam predicted as Scam [Risk score >= 60])
    fp = 0  # False Positives (Legit predicted as Scam)
    tn = 0  # True Negatives (Legit predicted as Safe/Caution [Risk score < 60])
    fn = 0  # False Negatives (Scam predicted as Safe/Caution)

    category_stats: Dict[str, Dict[str, int]] = {}
    latencies: List[float] = []

    for item in dataset:
        item_id = item["id"]
        true_label = item["label"].lower()
        text = item["text"]
        cat = item.get("category", "General")

        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "correct": 0}
        category_stats[cat]["total"] += 1

        t0 = time.time()
        rag_context = rag_engine.retrieve_context(text, top_k=3)
        analysis = risk_engine.calculate_score(text, rag_context)
        t1 = time.time()
        latencies.append((t1 - t0) * 1000)

        score = analysis["risk_score"]
        # Positive prediction = Risk score >= 60 (High Scam Risk or Critical Threat)
        predicted_is_scam = score >= 60

        is_scam = true_label in ["scam", "fraud"]

        if is_scam and predicted_is_scam:
            tp += 1
            category_stats[cat]["correct"] += 1
        elif not is_scam and not predicted_is_scam:
            tn += 1
            category_stats[cat]["correct"] += 1
        elif not is_scam and predicted_is_scam:
            fp += 1
        elif is_scam and not predicted_is_scam:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    accuracy = (tp + tn) / len(dataset) if len(dataset) > 0 else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print(f"\n[CONFUSION MATRIX]")
    print(f"  True Positives (TP) : {tp:2d} | False Positives (FP): {fp:2d}")
    print(f"  False Negatives (FN): {fn:2d} | True Negatives (TN) : {tn:2d}")

    print(f"\n[METRICS OVERVIEW]")
    print(f"  Overall Accuracy    : {accuracy * 100:.2f}%")
    print(f"  Precision           : {precision * 100:.2f}%")
    print(f"  Recall              : {recall * 100:.2f}%")
    print(f"  F1 Score            : {f1 * 100:.2f}%")
    print(f"  False Positive Rate : {fpr * 100:.2f}%")
    print(f"  Average Latency     : {avg_latency:.2f} ms")

    print(f"\n[PER-CATEGORY PERFORMANCE]")
    print(f"  {'Category':<32} | {'Correct':<8} | {'Total':<8} | {'Accuracy':<10}")
    print("  " + "-" * 64)
    for cat, stats in category_stats.items():
        cat_acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0.0
        print(f"  {cat:<32} | {stats['correct']:<8} | {stats['total']:<8} | {cat_acc:.1f}%")

    print("=" * 70)

if __name__ == "__main__":
    run_evaluation()
