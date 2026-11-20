import os
import json
import matplotlib.pyplot as plt
import numpy as np

def generate_charts():
    results_path = os.path.join(os.path.dirname(__file__), "adversarial_evaluation_results.json")
    if not os.path.exists(results_path):
        print(f"Results file not found at {results_path}")
        return

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    artifact_dir = r"C:\Users\Adity\.gemini\antigravity\brain\5be458e5-bb50-4d3c-b4b2-40755c64f1df"
    os.makedirs(artifact_dir, exist_ok=True)

    cm = data["confusion_matrix"]
    metrics = data["metrics"]
    v2_v3 = data["v2_vs_v3_comparison"]
    samples = data["per_sample_predictions"]
    timing = data["timing_breakdown"]

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    palette_primary = "#4f46e5"
    palette_secondary = "#06b6d4"
    palette_danger = "#ef4444"
    palette_success = "#10b981"
    palette_warning = "#f59e0b"

    # =========================================================================
    # Figure 1: Confusion Matrix
    # =========================================================================
    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=300)
    matrix = np.array([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
    im = ax.imshow(matrix, cmap="Blues", interpolation="nearest")

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Predicted Legit", "Predicted Scam"], fontsize=11, fontweight="bold")
    ax.set_yticklabels(["Actual Legit", "Actual Scam"], fontsize=11, fontweight="bold")
    ax.set_title(f"V3 Engine Adversarial Confusion Matrix (N={data['dataset_size']})\nAccuracy: {metrics['accuracy_percentage']}% | Recall: {metrics['recall_percentage']}%", fontsize=12, fontweight="bold", pad=14)

    for i in range(2):
        for j in range(2):
            val = matrix[i, j]
            label = ""
            if i == 0 and j == 0: label = f"TN\n{val}"
            elif i == 0 and j == 1: label = f"FP\n{val}"
            elif i == 1 and j == 0: label = f"FN\n{val}"
            elif i == 1 and j == 1: label = f"TP\n{val}"
            color = "white" if val > (matrix.max() / 2) else "#1e293b"
            ax.text(j, i, label, ha="center", va="center", color=color, fontsize=13, fontweight="bold")

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    fig1_path = os.path.join(artifact_dir, "fig1_adversarial_confusion_matrix.png")
    plt.savefig(fig1_path)
    plt.close()
    print(f"Generated: {fig1_path}")

    # =========================================================================
    # Figure 2: V2 vs V3 Detection on Adversarial Scams
    # =========================================================================
    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    categories = ["V2 Rule Engine", "V3 Semantic Hybrid"]
    scam_recall = [v2_v3["v2_scam_recall_percentage"], v2_v3["v3_scam_recall_percentage"]]
    colors = ["#94a3b8", palette_primary]
    
    bars = ax.bar(categories, scam_recall, color=colors, width=0.45, edgecolor="#1e293b", linewidth=1.2)
    ax.set_ylabel("Adversarial Scam Recall (%)", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 105)
    ax.set_title("Adversarial Scam Detection: V2 Heuristics vs V3 Hybrid", fontsize=12, fontweight="bold", pad=12)

    for bar, val in zip(bars, scam_recall):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 2.5, f"{val:.1f}%", ha="center", va="bottom", fontsize=12, fontweight="bold")

    lift = v2_v3["semantic_lift_percentage"]
    ax.annotate(f"+{lift:.1f}% Semantic Lift\n(Zero-Shot Reasoning)",
                xy=(1, v2_v3["v3_scam_recall_percentage"]),
                xytext=(0.4, 65),
                arrowprops=dict(facecolor=palette_success, shrink=0.08, width=2, headwidth=8),
                fontsize=10, fontweight="bold", color="#065f46",
                bbox=dict(boxstyle="round,pad=0.4", fc="#d1fae5", ec="#10b981", lw=1.2))

    plt.tight_layout()
    fig2_path = os.path.join(artifact_dir, "fig2_adversarial_v2_vs_v3_comparison.png")
    plt.savefig(fig2_path)
    plt.close()
    print(f"Generated: {fig2_path}")

    # =========================================================================
    # Figure 3: Score Distribution & Decision Threshold
    # =========================================================================
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    scam_scores = [s["v3_score"] for s in samples if s["true_label"] in ["scam", "fraud"]]
    legit_scores = [s["v3_score"] for s in samples if s["true_label"] not in ["scam", "fraud"]]

    bins = np.linspace(0, 100, 11)
    ax.hist(legit_scores, bins=bins, alpha=0.65, label="Legitimate Messages", color=palette_secondary, edgecolor="#0e7490")
    ax.hist(scam_scores, bins=bins, alpha=0.65, label="Scam Messages", color=palette_danger, edgecolor="#b91c1c")

    ax.axvline(x=60, color="#1e293b", linestyle="--", linewidth=2, label="Decision Threshold (60)")
    ax.set_xlabel("V3 Risk Score (0-100)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Message Count", fontsize=11, fontweight="bold")
    ax.set_title("V3 Risk Score Separation on Adversarial & Ambiguous Corpus", fontsize=12, fontweight="bold", pad=12)
    ax.legend(loc="upper center", frameon=True, fontsize=10)

    plt.tight_layout()
    fig3_path = os.path.join(artifact_dir, "fig3_adversarial_score_distribution.png")
    plt.savefig(fig3_path)
    plt.close()
    print(f"Generated: {fig3_path}")

    # =========================================================================
    # Figure 4: Error Breakdown & Per-Difficulty Performance
    # =========================================================================
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    outcomes = {"True Positive (TP)": cm["tp"], "True Negative (TN)": cm["tn"], "False Positive (FP)": cm["fp"], "False Negative (FN)": cm["fn"]}
    colors_outcomes = [palette_success, "#3b82f6", palette_warning, palette_danger]
    
    bars = ax.bar(outcomes.keys(), outcomes.values(), color=colors_outcomes, width=0.5, edgecolor="#1e293b", linewidth=1.2)
    ax.set_ylabel("Sample Count", fontsize=11, fontweight="bold")
    ax.set_title(f"Prediction Breakdown Across 20 Adversarial Cases\nCorrect: {cm['tp']+cm['tn']} | Errors: {cm['fp']+cm['fn']}", fontsize=12, fontweight="bold", pad=12)

    for bar, val in zip(bars, outcomes.values()):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.2, f"{val}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    plt.tight_layout()
    fig4_path = os.path.join(artifact_dir, "fig4_adversarial_error_breakdown.png")
    plt.savefig(fig4_path)
    plt.close()
    print(f"Generated: {fig4_path}")

    # =========================================================================
    # Figure 5: Latency Breakdown (Local Heuristics/RAG vs Gemini LLM API)
    # =========================================================================
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
    components = ["Local Engine & RAG", "Gemini LLM Call", "Total Pipeline"]
    latencies = [timing["mean_local_latency_ms"], timing["mean_gemini_latency_ms"], timing["mean_total_latency_ms"]]
    colors_lat = [palette_secondary, palette_primary, "#6366f1"]

    bars = ax.bar(components, latencies, color=colors_lat, width=0.45, edgecolor="#1e293b", linewidth=1.2)
    ax.set_ylabel("Mean Latency (ms)", fontsize=11, fontweight="bold")
    ax.set_title("V3 Hybrid Engine Latency Attribution", fontsize=12, fontweight="bold", pad=12)

    for bar, val in zip(bars, latencies):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 15, f"{val:.1f} ms", ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()
    fig5_path = os.path.join(artifact_dir, "fig5_adversarial_latency_attribution.png")
    plt.savefig(fig5_path)
    plt.close()
    print(f"Generated: {fig5_path}")

if __name__ == "__main__":
    generate_charts()
