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

from risk_engine import risk_engine
from rag_engine import rag_engine

def run_detailed_eval():
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset.json")
    kb_path = os.path.join(backend_dir, "knowledge_base.json")
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    with open(kb_path, "r", encoding="utf-8") as f:
        knowledge_base = json.load(f)

    # 1. Check Data Leakage between eval dataset and knowledge base
    kb_texts = {item["pattern_text"].strip().lower() for item in knowledge_base}
    leakage_count = 0
    leaked_items = []
    
    for item in dataset:
        text_clean = item["text"].strip().lower()
        if text_clean in kb_texts or any(text_clean in kb_text or kb_text in text_clean for kb_text in kb_texts):
            leakage_count += 1
            leaked_items.append(item["id"])

    # 2. Per-sample Prediction Execution & Timing Breakdown
    results = []
    category_metrics: Dict[str, Dict[str, int]] = {}
    
    total_rag_latencies = []
    total_risk_engine_latencies = []
    total_sample_latencies = []

    tp, fp, tn, fn = 0, 0, 0, 0
    false_negatives = []

    for item in dataset:
        item_id = item["id"]
        category = item["category"]
        true_label = item["label"].lower()
        text = item["text"]

        if category not in category_metrics:
            category_metrics[category] = {"total": 0, "tp": 0, "fp": 0, "tn": 0, "fn": 0}
        category_metrics[category]["total"] += 1

        # RAG timing
        t_rag_start = time.perf_counter()
        rag_context = rag_engine.retrieve_context(text, top_k=3)
        t_rag_end = time.perf_counter()
        rag_latency_ms = (t_rag_end - t_rag_start) * 1000

        # Risk Engine timing
        t_risk_start = time.perf_counter()
        analysis = risk_engine.calculate_score(text, rag_context)
        t_risk_end = time.perf_counter()
        risk_latency_ms = (t_risk_end - t_risk_start) * 1000

        total_latency_ms = rag_latency_ms + risk_latency_ms

        total_rag_latencies.append(rag_latency_ms)
        total_risk_engine_latencies.append(risk_latency_ms)
        total_sample_latencies.append(total_latency_ms)

        score = analysis["risk_score"]
        risk_level = analysis["risk_level"]
        predicted_is_scam = score >= 60
        predicted_label = "scam" if predicted_is_scam else "legitimate"

        is_actual_scam = true_label in ["scam", "fraud"]

        status = ""
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
        elif is_actual_scam and not predicted_is_scam:
            fn += 1
            category_metrics[category]["fn"] += 1
            status = "FN"
            false_negatives.append({
                "id": item_id,
                "category": category,
                "text": text,
                "score": score,
                "risk_level": risk_level,
                "extracted_indicators": analysis.get("extracted_indicators", []),
                "score_breakdown": analysis.get("score_breakdown", []),
                "rag_matches": [m["title"] for m in rag_context]
            })

        results.append({
            "id": item_id,
            "category": category,
            "true_label": true_label,
            "predicted_label": predicted_label,
            "score": score,
            "risk_level": risk_level,
            "status": status,
            "rag_latency_ms": round(rag_latency_ms, 2),
            "risk_engine_latency_ms": round(risk_latency_ms, 2),
            "total_latency_ms": round(total_latency_ms, 2),
            "text": text
        })

    # Calculations
    total_samples = len(dataset)
    scam_count = tp + fn
    legit_count = tn + fp

    accuracy = (tp + tn) / total_samples
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    total_sample_latencies.sort()
    p50_latency = statistics.median(total_sample_latencies)
    p95_idx = int(len(total_sample_latencies) * 0.95)
    p95_latency = total_sample_latencies[p95_idx]
    mean_latency = statistics.mean(total_sample_latencies)

    # 3. Save JSON and CSV Artifacts
    json_path = os.path.join(os.path.dirname(__file__), "evaluation_results.json")
    csv_path = os.path.join(os.path.dirname(__file__), "evaluation_results.csv")

    summary_payload = {
        "dataset_size": total_samples,
        "scam_samples": scam_count,
        "legitimate_samples": legit_count,
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn
        },
        "metrics": {
            "accuracy": round(accuracy, 4),
            "accuracy_formula": f"({tp} + {tn}) / {total_samples}",
            "precision": round(precision, 4),
            "precision_formula": f"{tp} / ({tp} + {fp})",
            "recall": round(recall, 4),
            "recall_formula": f"{tp} / ({tp} + {fn})",
            "f1_score": round(f1, 4),
            "specificity": round(specificity, 4),
            "specificity_formula": f"{tn} / ({tn} + {fp})",
            "false_positive_rate": round(fpr, 4),
            "fpr_formula": f"{fp} / ({fp} + {tn})"
        },
        "timing_breakdown": {
            "mean_total_latency_ms": round(mean_latency, 2),
            "p50_latency_ms": round(p50_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "mean_rag_retrieval_ms": round(statistics.mean(total_rag_latencies), 2),
            "mean_risk_engine_ms": round(statistics.mean(total_risk_engine_latencies), 2),
            "includes_gemini_api_call": False,
            "includes_ocr_processing": False,
            "latency_note": "Evaluated in deterministic RAG local engine mode. Live Gemini API latency (~1.2-2.5s) and Tesseract OCR (~0.5-1.5s) are additional when triggered."
        },
        "data_leakage_audit": {
            "leakage_count": leakage_count,
            "leaked_sample_ids": leaked_items,
            "audit_comment": "Verified knowledge_base.json vs dataset.json. No exact text overlap detected." if leakage_count == 0 else f"Detected {leakage_count} overlapping items."
        },
        "category_breakdown": category_metrics,
        "false_negatives": false_negatives,
        "per_sample_predictions": results
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "category", "true_label", "predicted_label", "score", "risk_level", "status", "rag_latency_ms", "risk_engine_latency_ms", "total_latency_ms", "text"])
        writer.writeheader()
        writer.writerows(results)

    print(f"[SUCCESS] Deep evaluation complete.")
    print(f"  JSON Artifact: {json_path}")
    print(f"  CSV Artifact: {csv_path}")
    print(f"\nSummary:")
    print(f"  Total Samples: {total_samples} (Scam: {scam_count}, Legit: {legit_count})")
    print(f"  Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn}")
    print(f"  Accuracy: {accuracy*100:.2f}% ({tp+tn}/{total_samples})")
    print(f"  Precision: {precision*100:.2f}% ({tp}/{tp+fp})")
    print(f"  Recall: {recall*100:.2f}% ({tp}/{tp+fn})")
    print(f"  Specificity: {specificity*100:.2f}% ({tn}/{tn+fp})")
    print(f"  FPR: {fpr*100:.2f}% ({fp}/{fp+tn})")
    print(f"  Mean Latency: {mean_latency:.2f}ms (p50: {p50_latency:.2f}ms, p95: {p95_latency:.2f}ms)")
    print(f"  False Negatives Count: {len(false_negatives)}")
    print(f"  Data Leakage: {leakage_count} exact matches found.")

if __name__ == "__main__":
    run_detailed_eval()
