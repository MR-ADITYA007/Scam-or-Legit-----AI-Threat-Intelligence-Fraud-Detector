import os
import json
import matplotlib.pyplot as plt
import numpy as np

def generate_adversarial_100_charts():
    results_path = os.path.join(os.path.dirname(__file__), "adversarial_100_results.json")
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
    # Figure 1: Confusion Matrix (N=100)
    # =========================================================================
    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=300)
    matrix = np.array([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
    im = ax.imshow(matrix, cmap="Blues", interpolation="nearest")

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Predicted Legit", "Predicted Scam"], fontsize=11, fontweight="bold")
    ax.set_yticklabels(["Actual Legit", "Actual Scam"], fontsize=11, fontweight="bold")
    ax.set_title(f"V3 Hybrid Engine 100-Sample Confusion Matrix\nAccuracy: {metrics['accuracy_percentage']}% | Recall: {metrics['recall_percentage']}%", fontsize=12, fontweight="bold", pad=14)

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
    fig1_path = os.path.join(artifact_dir, "fig1_adversarial_100_confusion_matrix.png")
    plt.savefig(fig1_path)
    plt.close()
    print(f"Generated: {fig1_path}")

    # =========================================================================
    # Figure 2: V2 vs V3 Detection Lift on 50 Adversarial Scams
    # =========================================================================
    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    categories = ["V2 Rule Engine", "V3 Semantic Hybrid"]
    scam_recall = [v2_v3["v2_scam_recall_percentage"], v2_v3["v3_scam_recall_percentage"]]
    colors = ["#94a3b8", palette_primary]
    
    bars = ax.bar(categories, scam_recall, color=colors, width=0.45, edgecolor="#1e293b", linewidth=1.2)
    ax.set_ylabel("Adversarial Scam Recall (%)", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 105)
    ax.set_title(f"50 Adversarial Scams: V2 Rule Engine vs V3 Semantic Hybrid", fontsize=12, fontweight="bold", pad=12)

    for bar, val in zip(bars, scam_recall):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 2.5, f"{val:.1f}%", ha="center", va="bottom", fontsize=12, fontweight="bold")

    lift = v2_v3["semantic_lift_percentage"]
    ax.annotate(f"+{lift:.1f}% Semantic Lift\n(Zero-Shot LLM Reasoning)",
                xy=(1, v2_v3["v3_scam_recall_percentage"]),
                xytext=(0.35, 60),
                arrowprops=dict(facecolor=palette_success, shrink=0.08, width=2, headwidth=8),
                fontsize=10, fontweight="bold", color="#065f46",
                bbox=dict(boxstyle="round,pad=0.4", fc="#d1fae5", ec="#10b981", lw=1.2))

    plt.tight_layout()
    fig2_path = os.path.join(artifact_dir, "fig2_adversarial_100_v2_vs_v3_lift.png")
    plt.savefig(fig2_path)
    plt.close()
    print(f"Generated: {fig2_path}")

    # =========================================================================
    # Figure 3: Score Distribution & Decision Threshold (N=100)
    # =========================================================================
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    scam_scores = [s["v3_score"] for s in samples if s["true_label"] in ["scam", "fraud"]]
    legit_scores = [s["v3_score"] for s in samples if s["true_label"] not in ["scam", "fraud"]]

    bins = np.linspace(0, 100, 15)
    ax.hist(legit_scores, bins=bins, alpha=0.65, label=f"Legitimate Messages (N={len(legit_scores)})", color=palette_secondary, edgecolor="#0e7490")
    ax.hist(scam_scores, bins=bins, alpha=0.65, label=f"Scam Messages (N={len(scam_scores)})", color=palette_danger, edgecolor="#b91c1c")

    ax.axvline(x=60, color="#1e293b", linestyle="--", linewidth=2, label="Decision Threshold (60)")
    ax.set_xlabel("V3 Risk Score (0-100)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Frequency", fontsize=11, fontweight="bold")
    ax.set_title("V3 Risk Score Separation on 100 Adversarial & Ambiguous Samples", fontsize=12, fontweight="bold", pad=12)
    ax.legend(loc="upper center", frameon=True, fontsize=10)

    plt.tight_layout()
    fig3_path = os.path.join(artifact_dir, "fig3_adversarial_100_score_distribution.png")
    plt.savefig(fig3_path)
    plt.close()
    print(f"Generated: {fig3_path}")

    # =========================================================================
    # Figure 4: ROC and Precision-Recall Curves
    # =========================================================================
    fig, (ax_roc, ax_pr) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)
    
    thresholds = np.linspace(0, 100, 101)
    tprs, fprs, precisions, recalls = [], [], [], []
    
    actual_binary = [1 if s["true_label"] in ["scam", "fraud"] else 0 for s in samples]
    v3_scores = [s["v3_score"] for s in samples]
    total_pos = sum(actual_binary)
    total_neg = len(actual_binary) - total_pos

    for th in thresholds:
        cur_tp = sum(1 for i, s in enumerate(v3_scores) if s >= th and actual_binary[i] == 1)
        cur_fp = sum(1 for i, s in enumerate(v3_scores) if s >= th and actual_binary[i] == 0)
        cur_fn = total_pos - cur_tp
        cur_tn = total_neg - cur_fp
        
        tpr = cur_tp / total_pos if total_pos > 0 else 0
        fpr = cur_fp / total_neg if total_neg > 0 else 0
        p = cur_tp / (cur_tp + cur_fp) if (cur_tp + cur_fp) > 0 else 1.0
        r = cur_tp / total_pos if total_pos > 0 else 0
        
        tprs.append(tpr)
        fprs.append(fpr)
        precisions.append(p)
        recalls.append(r)

    # Sort for monotonic plotting
    roc_pairs = sorted(zip(fprs, tprs))
    sorted_fpr = [p[0] for p in roc_pairs]
    sorted_tpr = [p[1] for p in roc_pairs]
    def trapz_calc(y, x):
        return sum((x[i+1] - x[i]) * (y[i+1] + y[i]) / 2.0 for i in range(len(x)-1))

    auc_roc = abs(trapz_calc(sorted_tpr, sorted_fpr))

    ax_roc.plot(sorted_fpr, sorted_tpr, color=palette_primary, lw=2.5, label=f"V3 Hybrid (AUC = {auc_roc:.3f})")
    ax_roc.plot([0, 1], [0, 1], color="#94a3b8", linestyle="--", lw=1.5, label="Random Guess")
    ax_roc.set_xlabel("False Positive Rate", fontsize=10, fontweight="bold")
    ax_roc.set_ylabel("True Positive Rate (Recall)", fontsize=10, fontweight="bold")
    ax_roc.set_title("ROC Curve (N=100)", fontsize=11, fontweight="bold")
    ax_roc.legend(loc="lower right")

    pr_pairs = sorted(zip(recalls, precisions))
    sorted_r = [p[0] for p in pr_pairs]
    sorted_p = [p[1] for p in pr_pairs]
    auc_pr = abs(trapz_calc(sorted_p, sorted_r))

    ax_pr.plot(sorted_r, sorted_p, color=palette_secondary, lw=2.5, label=f"V3 PR (AUC = {auc_pr:.3f})")
    ax_pr.set_xlabel("Recall", fontsize=10, fontweight="bold")
    ax_pr.set_ylabel("Precision", fontsize=10, fontweight="bold")
    ax_pr.set_title("Precision-Recall Curve (N=100)", fontsize=11, fontweight="bold")
    ax_pr.legend(loc="lower left")

    plt.tight_layout()
    fig4_path = os.path.join(artifact_dir, "fig4_adversarial_100_roc_pr_curves.png")
    plt.savefig(fig4_path)
    plt.close()
    print(f"Generated: {fig4_path}")

    # =========================================================================
    # Figure 5: Latency Profile
    # =========================================================================
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
    components = ["Local Heuristics + RAG", "Gemini 3 Flash LLM", "Total Pipeline"]
    latencies = [timing["mean_local_latency_ms"], timing["mean_gemini_latency_ms"], timing["mean_total_latency_ms"]]
    colors_lat = [palette_secondary, palette_primary, "#6366f1"]

    bars = ax.bar(components, latencies, color=colors_lat, width=0.45, edgecolor="#1e293b", linewidth=1.2)
    ax.set_ylabel("Mean Latency (ms)", fontsize=11, fontweight="bold")
    ax.set_title("Mean Latency Profile Across 100 Adversarial Cases", fontsize=12, fontweight="bold", pad=12)

    for bar, val in zip(bars, latencies):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 15, f"{val:.1f} ms", ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()
    fig5_path = os.path.join(artifact_dir, "fig5_adversarial_100_latency_profile.png")
    plt.savefig(fig5_path)
    plt.close()
    print(f"Generated: {fig5_path}")

if __name__ == "__main__":
    generate_adversarial_100_charts()
