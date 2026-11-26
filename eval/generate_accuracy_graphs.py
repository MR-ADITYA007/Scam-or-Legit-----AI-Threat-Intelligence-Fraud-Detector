import os
import json
import matplotlib.pyplot as plt
import numpy as np

def generate_accuracy_graphs():
    artifact_dir = r"C:\Users\Adity\.gemini\antigravity\brain\5be458e5-bb50-4d3c-b4b2-40755c64f1df"
    os.makedirs(artifact_dir, exist_ok=True)

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    palette_primary = "#4f46e5"     # Indigo
    palette_secondary = "#06b6d4"   # Cyan
    palette_success = "#10b981"     # Emerald
    palette_warning = "#f59e0b"     # Amber
    palette_danger = "#ef4444"      # Rose

    # =========================================================================
    # Accuracy Graph 1: Cross-Benchmark Comprehensive Accuracy & Metric Comparison
    # =========================================================================
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    
    benchmarks = [
        "Heldout Baseline\n(N=60, Standard)",
        "Fresh Unseen\n(N=30, Modern)",
        "Adversarial Pilot\n(N=20, Edge Cases)",
        "Adversarial Full\n(N=100, Stress Test)"
    ]
    
    accuracies = [96.67, 96.67, 85.00, 84.00]
    recalls = [93.33, 93.33, 90.00, 80.00]
    precisions = [100.00, 100.00, 81.82, 86.96]
    specificities = [100.00, 100.00, 80.00, 88.00]
    f1_scores = [96.55, 96.55, 85.71, 83.33]

    x = np.arange(len(benchmarks))
    width = 0.16

    r1 = ax.bar(x - 2*width + width/2, accuracies, width, label="Accuracy (%)", color="#6366f1", edgecolor="#312e81")
    r2 = ax.bar(x - width + width/2, recalls, width, label="Recall / Sensitivity (%)", color="#10b981", edgecolor="#064e3b")
    r3 = ax.bar(x + width/2, precisions, width, label="Precision (%)", color="#06b6d4", edgecolor="#164e63")
    r4 = ax.bar(x + width + width/2, specificities, width, label="Specificity (%)", color="#8b5cf6", edgecolor="#4c1d95")
    r5 = ax.bar(x + 2*width + width/2, f1_scores, width, label="F1-Score (%)", color="#f43f5e", edgecolor="#881337")

    ax.set_ylabel("Performance Metric Score (%)", fontsize=11, fontweight="bold")
    ax.set_title("V3 Hybrid Engine: Comprehensive Cross-Benchmark Accuracy & Performance Profile", fontsize=12, fontweight="bold", pad=14)
    ax.set_xticks(x)
    ax.set_xticklabels(benchmarks, fontsize=10, fontweight="bold")
    ax.set_ylim(60, 108)
    ax.axhline(80, color="#94a3b8", linestyle="--", alpha=0.7, label="Target Production Boundary (80%)")
    ax.legend(loc="lower left", frameon=True, fontsize=9, ncol=3)

    for bar in r1:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 1.2, f"{yval:.1f}%", ha='center', va='bottom', fontsize=8.5, fontweight='bold', color="#4338ca")

    plt.tight_layout()
    fig_acc1_path = os.path.join(artifact_dir, "fig_acc1_cross_benchmark_comparison.png")
    plt.savefig(fig_acc1_path)
    plt.close()
    print(f"Generated: {fig_acc1_path}")

    # =========================================================================
    # Accuracy Graph 2: Accuracy vs Decision Threshold (Theta) Curve
    # =========================================================================
    results_100_path = os.path.join(os.path.dirname(__file__), "adversarial_100_results.json")
    results_fresh_path = os.path.join(os.path.dirname(__file__), "fresh_benchmark_results.json")
    
    samples_100 = []
    if os.path.exists(results_100_path):
        with open(results_100_path, "r", encoding="utf-8") as f:
            samples_100 = json.load(f).get("per_sample_predictions", [])

    thresholds = np.linspace(10, 90, 81)
    acc_100 = []
    f1_100 = []
    prec_100 = []
    rec_100 = []

    if samples_100:
        actual_pos = [1 if s["true_label"] in ["scam", "fraud"] else 0 for s in samples_100]
        scores_100 = [s["v3_score"] for s in samples_100]
        total_n = len(samples_100)
        tot_pos = sum(actual_pos)
        tot_neg = total_n - tot_pos

        for th in thresholds:
            tp = sum(1 for i, sc in enumerate(scores_100) if sc >= th and actual_pos[i] == 1)
            tn = sum(1 for i, sc in enumerate(scores_100) if sc < th and actual_pos[i] == 0)
            fp = sum(1 for i, sc in enumerate(scores_100) if sc >= th and actual_pos[i] == 0)
            fn = sum(1 for i, sc in enumerate(scores_100) if sc < th and actual_pos[i] == 1)

            acc = (tp + tn) / total_n * 100
            p = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 100.0
            r = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0.0
            f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0

            acc_100.append(acc)
            f1_100.append(f1)
            prec_100.append(p)
            rec_100.append(r)

    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    ax.plot(thresholds, acc_100, label="Overall Accuracy (%)", color="#6366f1", lw=2.8)
    ax.plot(thresholds, f1_100, label="F1-Score (%)", color="#f43f5e", lw=2.2, linestyle="-.")
    ax.plot(thresholds, prec_100, label="Precision (%)", color="#06b6d4", lw=2.0, linestyle=":")
    ax.plot(thresholds, rec_100, label="Recall (%)", color="#10b981", lw=2.0, linestyle="--")

    ax.axvline(x=60, color="#1e293b", linestyle="-", lw=1.8, label="Operating Decision Boundary (Theta=60)")
    ax.scatter([60], [84.0], color="#6366f1", s=80, zorder=5)
    ax.annotate("Operating Accuracy: 84.0%\nF1: 83.3%",
                xy=(60, 84.0), xytext=(65, 68),
                arrowprops=dict(facecolor="#4f46e5", shrink=0.08, width=1.5, headwidth=6),
                fontsize=9.5, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.4", fc="#e0e7ff", ec="#6366f1", lw=1.2))

    ax.set_xlabel("Risk Score Decision Threshold (Theta)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Metric Score (%)", fontsize=11, fontweight="bold")
    ax.set_title("V3 Hybrid Engine: Accuracy & Operating Trade-off vs Decision Threshold (N=100)", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylim(40, 105)
    ax.legend(loc="lower left", frameon=True, fontsize=9.5)

    plt.tight_layout()
    fig_acc2_path = os.path.join(artifact_dir, "fig_acc2_accuracy_vs_decision_threshold.png")
    plt.savefig(fig_acc2_path)
    plt.close()
    print(f"Generated: {fig_acc2_path}")

    # =========================================================================
    # Accuracy Graph 3: Domain / Category Level Accuracy Matrix
    # =========================================================================
    domains = [
        "Banking & KYC",
        "Delivery & Logistics",
        "E-Commerce & Retail",
        "Enterprise IT & Auth",
        "Government & Tax",
        "Healthcare & Lab",
        "P2P, Romance & Social",
        "Crypto & Investment",
        "Utility & Municipal",
        "Travel & Transport"
    ]
    
    # Combined across fresh & adversarial 100
    dom_accuracy = [92.3, 85.7, 90.0, 83.3, 87.5, 75.0, 72.7, 88.9, 83.3, 88.9]
    v2_dom_accuracy = [69.2, 57.1, 70.0, 50.0, 62.5, 50.0, 36.4, 44.4, 50.0, 55.6]

    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    y = np.arange(len(domains))
    height = 0.38

    b1 = ax.barh(y + height/2, dom_accuracy, height, label="V3 Hybrid Semantic Model", color=palette_primary, edgecolor="#312e81")
    b2 = ax.barh(y - height/2, v2_dom_accuracy, height, label="V2 Deterministic Rule Engine", color="#94a3b8", edgecolor="#334155")

    ax.set_xlabel("Accuracy by Threat Domain (%)", fontsize=11, fontweight="bold")
    ax.set_title("Domain-Specific Accuracy Breakdown: V2 Heuristics vs V3 Semantic Hybrid", fontsize=12, fontweight="bold", pad=12)
    ax.set_yticks(y)
    ax.set_yticklabels(domains, fontsize=10, fontweight="bold")
    ax.set_xlim(0, 105)
    ax.legend(loc="lower right", frameon=True, fontsize=10)

    for bar in b1:
        val = bar.get_width()
        ax.text(val + 1.2, bar.get_y() + bar.get_height()/2, f"{val:.1f}%", ha='left', va='center', fontsize=9, fontweight='bold', color="#3730a3")

    plt.tight_layout()
    fig_acc3_path = os.path.join(artifact_dir, "fig_acc3_category_accuracy_matrix.png")
    plt.savefig(fig_acc3_path)
    plt.close()
    print(f"Generated: {fig_acc3_path}")

if __name__ == "__main__":
    generate_accuracy_graphs()
