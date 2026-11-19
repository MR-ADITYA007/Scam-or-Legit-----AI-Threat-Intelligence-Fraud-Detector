import os
import sys
import json
import time
import csv
import statistics
from typing import Dict, Any, List

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from llm_analyzer import analyzer
from rag_engine import rag_engine

def run_blind_evaluation():
    dataset_path = os.path.join(os.path.dirname(__file__), "blind_dataset.json")
    
    if not os.path.exists(dataset_path):
        print(f"[ERROR] Blind dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    results = []
    category_metrics = {}
    
    total_latencies = []
    gemini_latencies = []
    local_latencies = []

    tp, fp, tn, fn = 0, 0, 0, 0
    false_negatives = []
    false_positives = []
    
    # Also track v2 vs v3
    v2_tp, v2_fn = 0, 0

    print(f"Starting blind evaluation on {len(dataset)} samples...")

    for idx, item in enumerate(dataset):
        if idx > 0:
            time.sleep(10) # Prevent Gemini Free Tier 429 errors
        item_id = item["id"]
        print(f"[{idx+1}/{len(dataset)}] Evaluating {item_id} ({item['category']})...", flush=True)
        category = item["category"]
        true_label = item["label"].lower()
        text = item["text"]
        
        if category not in category_metrics:
            category_metrics[category] = {"total": 0, "tp": 0, "fp": 0, "tn": 0, "fn": 0}
        category_metrics[category]["total"] += 1

        t_start = time.perf_counter()
        
        rag_context = rag_engine.retrieve_context(text, top_k=3)
        analysis = analyzer.analyze(text, rag_context)
        
        t_end = time.perf_counter()
        latency_ms = (t_end - t_start) * 1000
        total_latencies.append(latency_ms)

        score = analysis["risk_score"]
        v2_score = analysis.get("analysis_metadata", {}).get("deterministic_risk_score", score)
        
        semantic_score = analysis.get("analysis_metadata", {}).get("semantic_risk_score", "N/A")
        
        predicted_is_scam = score >= 60
        v2_predicted_is_scam = v2_score >= 60

        is_actual_scam = true_label in ["scam", "fraud"]

        status = ""
        if is_actual_scam:
            if v2_predicted_is_scam:
                v2_tp += 1
            else:
                v2_fn += 1

        gemini_active = analysis.get("analysis_metadata", {}).get("gemini_active", False)
        fallback_status = analysis.get("analysis_metadata", {}).get("fallback_status", "None")
        semantic_evidence = analysis.get("semantic_evidence", {})

        # We also need to extract local RAG latency and gemini latency separately
        gemini_success_latency_ms = analysis.get("analysis_metadata", {}).get("gemini_success_latency_ms", 0.0)
        gemini_failed_latency_ms = analysis.get("analysis_metadata", {}).get("gemini_failed_latency_ms", 0.0)
        local_latency_ms = latency_ms - gemini_success_latency_ms - gemini_failed_latency_ms

        gemini_latencies.append(gemini_success_latency_ms)
        local_latencies.append(local_latency_ms)

        # Keep secrets out of logs
        record = {
            "id": item_id,
            "category": category,
            "v2_score": v2_score,
            "semantic_score": semantic_score,
            "v3_score": score,
            "predicted_label": "scam" if predicted_is_scam else "legitimate",
            "gemini_invoked": gemini_active,
            "fallback_status": fallback_status,
            "semantic_evidence": semantic_evidence,
            "total_latency_ms": round(latency_ms, 2),
            "gemini_success_latency_ms": round(gemini_success_latency_ms, 2),
            "gemini_failed_latency_ms": round(gemini_failed_latency_ms, 2),
            "local_latency_ms": round(local_latency_ms, 2)
        }
        if is_actual_scam and predicted_is_scam:
            tp += 1
            category_metrics[category]["tp"] += 1
            status = "TP"
        elif not is_actual_scam and not predicted_is_scam:
            tn += 1
            category_metrics[category]["tn"] += 1
            status = "TN"
        elif not is_actual_scam and predicted_is_scam:
            fp += 1
            category_metrics[category]["fp"] += 1
            status = "FP"
            false_positives.append(record)
        elif is_actual_scam and not predicted_is_scam:
            fn += 1
            category_metrics[category]["fn"] += 1
            status = "FN"
            false_negatives.append(record)

        # Include ground truth label only in the artifact
        record["true_label"] = true_label
        record["status"] = status
        
        results.append(record)

    total_samples = len(dataset)
    accuracy = (tp + tn) / total_samples
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    
    v2_recall = v2_tp / (v2_tp + v2_fn) if (v2_tp + v2_fn) > 0 else 0.0

    mean_latency = statistics.mean(total_latencies)

    json_out_path = os.path.join(os.path.dirname(__file__), "blind_evaluation_results.json")
    
    summary_payload = {
        "evaluation_type": "V3 Semantic Evidence Blind Evaluation",
        "dataset_name": "blind_dataset.json",
        "dataset_size": total_samples,
        "scam_samples": tp + fn,
        "legitimate_samples": tn + fp,
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn
        },
        "metrics": {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "specificity": tn / (tn + fp) if (tn + fp) > 0 else 0.0,
            "false_positive_rate": round(fpr, 4),
            "f1_score": round(f1, 4),
        },
        "v2_comparison": {
            "v2_scam_recall": round(v2_recall, 4),
            "v3_scam_recall": round(recall, 4)
        },
        "timing_breakdown": {
            "mean_total_latency_ms": round(mean_latency, 2),
            "mean_gemini_success_latency_ms": round(statistics.mean([r["gemini_success_latency_ms"] for r in results]), 2),
            "mean_gemini_failed_latency_ms": round(statistics.mean([r["gemini_failed_latency_ms"] for r in results]), 2),
            "mean_local_latency_ms": round(statistics.mean([r["local_latency_ms"] for r in results]), 2)
        },
        "category_breakdown": category_metrics,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "per_sample_predictions": results
    }

    with open(json_out_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)

    print("=" * 70)
    print(f"   SCAM OR LEGIT? — V3 BLIND EVALUATION REPORT (N={total_samples})")
    print("=" * 70)
    print(f"  Artifact JSON : {json_out_path}")
    print(f"  True Positives (TP) : {tp:2d} | False Positives (FP): {fp:2d}")
    print(f"  False Negatives (FN): {fn:2d} | True Negatives (TN) : {tn:2d}")
    
    print(f"\n[V2 (DETERMINISTIC) vs V3 (SEMANTIC) COMPARISON]")
    print(f"  V2 Scam Recall     : {v2_recall * 100:.2f}%")
    print(f"  V3 Scam Recall     : {recall * 100:.2f}%")
    
    print(f"\n[V3 PERFORMANCE METRICS]")
    print(f"  Accuracy           : {accuracy * 100:.2f}%")
    print(f"  Precision          : {precision * 100:.2f}%")
    print(f"  Recall             : {recall * 100:.2f}%")
    print(f"  False Positive Rate: {fpr * 100:.2f}%")
    print(f"  F1 Score           : {f1 * 100:.2f}%")
    print(f"  Mean Latency (ms)  : {mean_latency:.2f} ms")

if __name__ == "__main__":
    run_blind_evaluation()
