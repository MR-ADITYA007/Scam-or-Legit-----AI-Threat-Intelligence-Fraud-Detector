import os
import sys
import json
import time
import statistics
from typing import Dict, Any, List

os.environ["GEMINI_MODEL_NAME"] = "gemini-flash-lite-latest"

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

import llm_analyzer
llm_analyzer.GEMINI_MODEL_NAME = "gemini-flash-lite-latest"
from llm_analyzer import analyzer
from rag_engine import rag_engine

def run_adversarial_100_evaluation():
    dataset_path = os.path.join(os.path.dirname(__file__), "adversarial_100_dataset.json")
    json_out_path = os.path.join(os.path.dirname(__file__), "adversarial_100_results.json")
    
    if not os.path.exists(dataset_path):
        print(f"[ERROR] Dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # Resume from existing results if available
    results = []
    completed_ids = set()
    category_metrics = {}
    total_latencies = []
    gemini_latencies = []
    local_latencies = []
    tp, fp, tn, fn = 0, 0, 0, 0
    v2_tp, v2_fn = 0, 0

    if os.path.exists(json_out_path):
        try:
            with open(json_out_path, "r", encoding="utf-8") as f:
                prev_data = json.load(f)
                prev_preds = prev_data.get("per_sample_predictions", [])
                for p in prev_preds:
                    results.append(p)
                    completed_ids.add(p["id"])
                    cat = p["category"]
                    if cat not in category_metrics:
                        category_metrics[cat] = {"total": 0, "tp": 0, "fp": 0, "tn": 0, "fn": 0}
                    category_metrics[cat]["total"] += 1
                    
                    st = p["status"]
                    if st == "TP":
                        tp += 1
                        category_metrics[cat]["tp"] += 1
                    elif st == "TN":
                        tn += 1
                        category_metrics[cat]["tn"] += 1
                    elif st == "FP":
                        fp += 1
                        category_metrics[cat]["fp"] += 1
                    elif st == "FN":
                        fn += 1
                        category_metrics[cat]["fn"] += 1

                    if p["true_label"] in ["scam", "fraud"]:
                        if p.get("v2_score", 0) >= 60:
                            v2_tp += 1
                        else:
                            v2_fn += 1

                    total_latencies.append(p.get("total_latency_ms", 5000.0))
                    gemini_latencies.append(p.get("gemini_latency_ms", 4500.0))
                    local_latencies.append(p.get("local_latency_ms", 500.0))
            print(f"[RESUME] Loaded {len(completed_ids)} completed samples from {json_out_path}")
        except Exception as e:
            print(f"[WARN] Could not parse existing results: {e}. Starting fresh.")
            results = []
            completed_ids = set()

    print(f"Starting Live V3 Evaluation on {len(dataset)} Adversarial & Ambiguous Samples...")
    print(f"Using model: {llm_analyzer.GEMINI_MODEL_NAME}")
    print("=" * 80)

    for idx, item in enumerate(dataset):
        item_id = item["id"]
        if item_id in completed_ids:
            continue

        time.sleep(4.0)  # Rate limit safety

        category = item["category"]
        true_label = item["label"].lower()
        text = item["text"]
        difficulty = item.get("difficulty", "")
        
        if category not in category_metrics:
            category_metrics[category] = {"total": 0, "tp": 0, "fp": 0, "tn": 0, "fn": 0}
        category_metrics[category]["total"] += 1

        t_start = time.perf_counter()
        
        # Live multi-layer pipeline execution
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

        if is_actual_scam:
            if v2_predicted_is_scam:
                v2_tp += 1
            else:
                v2_fn += 1

        gemini_active = analysis.get("analysis_metadata", {}).get("gemini_active", False)
        fallback_status = analysis.get("analysis_metadata", {}).get("fallback_status", "None")
        gemini_success_latency_ms = analysis.get("analysis_metadata", {}).get("gemini_success_latency_ms", 0.0)
        gemini_failed_latency_ms = analysis.get("analysis_metadata", {}).get("gemini_failed_latency_ms", 0.0)
        local_latency_ms = max(0.0, latency_ms - gemini_success_latency_ms - gemini_failed_latency_ms)

        gemini_latencies.append(gemini_success_latency_ms)
        local_latencies.append(local_latency_ms)

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

        record = {
            "id": item_id,
            "category": category,
            "difficulty": difficulty,
            "true_label": true_label,
            "v2_score": v2_score,
            "semantic_score": semantic_score,
            "v3_score": score,
            "predicted_label": "scam" if predicted_is_scam else "legitimate",
            "status": status,
            "gemini_invoked": gemini_active,
            "fallback_status": fallback_status,
            "summary": analysis.get("summary", ""),
            "red_flags": analysis.get("red_flags", []),
            "total_latency_ms": round(latency_ms, 2),
            "gemini_latency_ms": round(gemini_success_latency_ms, 2),
            "local_latency_ms": round(local_latency_ms, 2)
        }
        results.append(record)
        completed_ids.add(item_id)

        processed = len(results)
        current_acc = (tp + tn) / processed
        print(f"[{processed:03d}/{len(dataset):03d}] {item_id:<14} | True: {true_label:<10} | Pred: {record['predicted_label']:<10} | {status:<2} | V3: {score:3d} (V2: {v2_score:2d}) | Acc: {current_acc*100:5.1f}% | {category[:22]}", flush=True)

        # Periodically update the output file incrementally
        if processed % 5 == 0 or processed == len(dataset):
            total_samples = processed
            scam_count = tp + fn
            legit_count = tn + fp
            accuracy = (tp + tn) / total_samples
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            v2_recall = v2_tp / (v2_tp + v2_fn) if (v2_tp + v2_fn) > 0 else 0.0

            summary_payload = {
                "evaluation_type": "Adversarial & Ambiguous Large-Scale Benchmark (N=100)",
                "dataset_name": "adversarial_100_dataset.json",
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
                    "accuracy_percentage": round(accuracy * 100, 2),
                    "precision": round(precision, 4),
                    "precision_percentage": round(precision * 100, 2),
                    "recall": round(recall, 4),
                    "recall_percentage": round(recall * 100, 2),
                    "specificity": round(specificity, 4),
                    "specificity_percentage": round(specificity * 100, 2),
                    "false_positive_rate": round(fpr, 4),
                    "fpr_percentage": round(fpr * 100, 2),
                    "f1_score": round(f1, 4)
                },
                "v2_vs_v3_comparison": {
                    "v2_scam_recall": round(v2_recall, 4),
                    "v2_scam_recall_percentage": round(v2_recall * 100, 2),
                    "v3_scam_recall": round(recall, 4),
                    "v3_scam_recall_percentage": round(recall * 100, 2),
                    "semantic_lift_percentage": round((recall - v2_recall) * 100, 2)
                },
                "timing_breakdown": {
                    "mean_total_latency_ms": round(statistics.mean(total_latencies), 2),
                    "mean_gemini_latency_ms": round(statistics.mean(gemini_latencies), 2),
                    "mean_local_latency_ms": round(statistics.mean(local_latencies), 2)
                },
                "category_breakdown": category_metrics,
                "per_sample_predictions": results
            }

            with open(json_out_path, "w", encoding="utf-8") as f:
                json.dump(summary_payload, f, indent=2)

    total_samples = len(results)
    accuracy = (tp + tn) / total_samples
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    v2_recall = v2_tp / (v2_tp + v2_fn) if (v2_tp + v2_fn) > 0 else 0.0

    print("=" * 80)
    print(f"   SCAM OR LEGIT? — 100-SAMPLE ADVERSARIAL BENCHMARK COMPLETE")
    print("=" * 80)
    print(f"  Artifact File       : {json_out_path}")
    print(f"  Confusion Matrix    : TP={tp} | FP={fp} | TN={tn} | FN={fn}")
    print(f"  Overall Accuracy    : {accuracy * 100:.2f}% ({tp+tn}/{total_samples})")
    print(f"  Precision           : {precision * 100:.2f}% ({tp}/{tp+fp})")
    print(f"  Recall (Sensitivity): {recall * 100:.2f}% ({tp}/{tp+fn})")
    print(f"  Specificity         : {specificity * 100:.2f}% ({tn}/{tn+fp})")
    print(f"  False Positive Rate : {fpr * 100:.2f}% ({fp}/{fp+tn})")
    print(f"  F1 Score            : {f1 * 100:.2f}%")
    print(f"\n[V2 (DETERMINISTIC) vs V3 (SEMANTIC HYBRID) COMPARISON]")
    print(f"  V2 Scam Recall      : {v2_recall * 100:.2f}%")
    print(f"  V3 Scam Recall      : {recall * 100:.2f}%")
    print("=" * 80)

if __name__ == "__main__":
    run_adversarial_100_evaluation()
