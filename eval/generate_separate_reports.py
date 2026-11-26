import os
import shutil
import base64
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, doc_title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.doc_title = doc_title
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        if self._pageNumber > 1:
            self.drawString(36, 805, self.doc_title)
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 800, 559, 800)

        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 42, 559, 42)
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(559, 30, page_str)
        self.drawString(36, 30, "ScamOrLegit V3 — AI Threat Intelligence & Fraud Detection")
        self.restoreState()


def b64_img(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    return ""


def generate_fresh_report():
    artifact_dir = r"C:\Users\Adity\.gemini\antigravity\brain\5be458e5-bb50-4d3c-b4b2-40755c64f1df"
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    # 1. Copy Markdown report
    src_md = os.path.join(artifact_dir, "fresh_unseen_benchmark_report.md")
    dst_md = os.path.join(reports_dir, "fresh_unseen_benchmark_report.md")
    if os.path.exists(src_md):
        shutil.copyfile(src_md, dst_md)
        print(f"Copied fresh MD to {dst_md}")

    # Image Paths
    img_cm = os.path.join(artifact_dir, "fig1_fresh_confusion_matrix.png")
    img_v2v3 = os.path.join(artifact_dir, "fig2_fresh_v2_vs_v3_comparison.png")
    img_cat = os.path.join(artifact_dir, "fig3_fresh_category_performance.png")
    img_score = os.path.join(artifact_dir, "fig4_fresh_score_spread.png")
    img_time = os.path.join(artifact_dir, "fig5_fresh_timing_resilience.png")

    # 2. Build PDF Report
    pdf_path = os.path.join(reports_dir, "fresh_unseen_benchmark_report.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=48
    )

    usable_width = 523.27
    styles = getSampleStyleSheet()

    c_primary = colors.HexColor("#1E1B4B")
    c_accent = colors.HexColor("#059669")     # Emerald theme for Fresh
    c_text = colors.HexColor("#0F172A")
    c_muted = colors.HexColor("#475569")
    c_border = colors.HexColor("#CBD5E1")
    c_bg_light = colors.HexColor("#F8FAFC")

    title_style = ParagraphStyle('DocTitle', fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=c_primary, spaceAfter=6)
    subtitle_style = ParagraphStyle('DocSub', fontName='Helvetica', fontSize=10.5, leading=14, textColor=c_muted, spaceAfter=12)
    h1_style = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=13, leading=17, textColor=c_accent, spaceBefore=14, spaceAfter=8, keepWithNext=True)
    body_style = ParagraphStyle('Body', fontName='Helvetica', fontSize=9, leading=13, textColor=c_text, spaceAfter=6)
    caption_style = ParagraphStyle('Cap', fontName='Helvetica-Oblique', fontSize=8, leading=11, textColor=c_muted, alignment=1, spaceBefore=4, spaceAfter=10)
    th_style = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white, alignment=1)
    tc_style = ParagraphStyle('TC', fontName='Helvetica', fontSize=7.5, leading=10, textColor=c_text)
    tc_bold = ParagraphStyle('TCB', fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=c_text)
    tc_center = ParagraphStyle('TCC', fontName='Helvetica', fontSize=7.5, leading=10, textColor=c_text, alignment=1)

    story = []

    badge = Table([[Paragraph("<font color='#059669'><b>FRESH UNSEEN BENCHMARK REPORT (N=30) • ZERO DISTRIBUTION LEAKAGE</b></font>", tc_style)]], colWidths=[usable_width])
    badge.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#ECFDF5")), ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#A7F3D0")), ('PADDING', (0,0), (-1,-1), 4)]))
    story.append(badge)
    story.append(Spacer(1, 6))

    story.append(Paragraph("ScamOrLegit V3: Fresh Unseen Dataset Benchmark Report", title_style))
    story.append(Paragraph("Out-of-Sample Empirical Evaluation across 15 Modern Scam Vectors and 15 Authentic Transactions", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=0, spaceAfter=8))

    kpis = [
        [
            Paragraph("<b>Overall Accuracy</b><br/><font size='14' color='#059669'><b>96.67%</b></font><br/><font size='6.5' color='#64748B'>29 / 30 Correct</font>", tc_center),
            Paragraph("<b>Precision</b><br/><font size='14' color='#0284C7'><b>100.00%</b></font><br/><font size='6.5' color='#64748B'>Zero False Positives</font>", tc_center),
            Paragraph("<b>Scam Recall</b><br/><font size='14' color='#4F46E5'><b>93.33%</b></font><br/><font size='6.5' color='#64748B'>14 / 15 Intercepted</font>", tc_center),
            Paragraph("<b>Semantic Lift</b><br/><font size='14' color='#D97706'><b>+66.67%</b></font><br/><font size='6.5' color='#64748B'>Over Heuristic V2</font>", tc_center)
        ]
    ]
    t_kpis = Table(kpis, colWidths=[usable_width/4.0]*4)
    t_kpis.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), c_bg_light), ('BOX', (0,0), (-1,-1), 1, c_border), ('INNERGRID', (0,0), (-1,-1), 0.5, c_border), ('PADDING', (0,0), (-1,-1), 6)]))
    story.append(t_kpis)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Section 1: Evaluation Setup & Measured Confusion Matrix", h1_style))
    story.append(Paragraph("To evaluate out-of-sample generalization without distribution leakage, 30 freshly authored samples were passed through the multi-layer hybrid engine. The test set comprises 15 contemporary scam vectors (CBI digital arrest, electricity bill cuts, Telegram stock pump, YouTube video tasks, IndiaPost smishing) and 15 clean consumer notifications.", body_style))

    if os.path.exists(img_cm):
        story.append(Image(img_cm, width=usable_width*0.7, height=210))
        story.append(Paragraph("Figure 1: Fresh Unseen Confusion Matrix (N=30) at Decision Boundary &Theta; = 60 (Accuracy: 96.67%, Precision: 100.00%).", caption_style))

    story.append(Paragraph("Section 2: V2 Deterministic vs. V3 Semantic Hybrid Lift", h1_style))
    story.append(Paragraph("Pure regex and keyword matching failed against 73.33% of modern scams because contemporary threat actors avoid textbook crude triggers. The V3 hybrid engine (ChromaDB RAG + Foundation LLM) caught 14 of 15 attacks (+66.67% lift) while preserving zero false alarms.", body_style))

    if os.path.exists(img_v2v3):
        story.append(Image(img_v2v3, width=usable_width*0.75, height=200))
        story.append(Paragraph("Figure 2: V2 Rule Engine (26.67%) vs. V3 Semantic Hybrid (93.33%) Threat Recall Comparison.", caption_style))

    story.append(PageBreak())

    story.append(Paragraph("Section 3: Per-Category Threat Breakdown & Score Spread", h1_style))
    if os.path.exists(img_cat):
        story.append(Image(img_cat, width=usable_width, height=200))
        story.append(Paragraph("Figure 3: Category-Level Detection Breakdown across 15 Emerging Scam Vectors.", caption_style))

    if os.path.exists(img_score):
        story.append(Image(img_score, width=usable_width*0.8, height=190))
        story.append(Paragraph("Figure 4: Risk Score Spread: 55-Point Safety Separation Between Legitimate Max and Operating Threshold.", caption_style))

    if os.path.exists(img_time):
        story.append(Image(img_time, width=usable_width*0.8, height=190))
        story.append(Paragraph("Figure 5: Timing Profile and Graceful Quota Fallback Resilience Audit.", caption_style))

    doc.build(story, canvasmaker=lambda *args, **kwargs: NumberedCanvas("ScamOrLegit V3 — Fresh Unseen Benchmark Report (N=30)", *args, **kwargs))
    print(f"Generated Fresh PDF at {pdf_path}")

    # 3. Build Standalone HTML Report
    b64_cm = b64_img(img_cm)
    b64_v2v3 = b64_img(img_v2v3)
    b64_cat = b64_img(img_cat)
    b64_score = b64_img(img_score)
    b64_time = b64_img(img_time)

    html_path = os.path.join(reports_dir, "fresh_unseen_benchmark_report.html")
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Fresh Unseen Benchmark Report (N=30) | ScamOrLegit V3</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{ --bg-primary: #0a0e17; --bg-surface: #111827; --border: #374151; --text-main: #f9fafb; --text-muted: #9ca3af; --emerald: #10b981; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg-primary); color: var(--text-main); font-family: 'Inter', sans-serif; line-height: 1.6; padding: 32px 20px; }}
    .wrapper {{ max-width: 1000px; margin: 0 auto; }}
    .action-bar {{ display: flex; justify-content: space-between; align-items: center; background: rgba(17, 24, 39, 0.8); border: 1px solid var(--border); padding: 12px 20px; border-radius: 12px; margin-bottom: 24px; position: sticky; top: 12px; z-index: 100; backdrop-filter: blur(10px); }}
    .print-btn {{ background: linear-gradient(135deg, #10b981, #059669); border: none; color: #fff; font-weight: 700; font-size: 0.85rem; padding: 10px 20px; border-radius: 8px; cursor: pointer; }}
    .header {{ background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 16px; padding: 36px; margin-bottom: 32px; }}
    .tag {{ display: inline-block; background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; color: #a7f3d0; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; padding: 4px 12px; border-radius: 999px; margin-bottom: 12px; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; color: #fff; margin-bottom: 8px; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px; }}
    .kpi-card {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: center; }}
    .kpi-val {{ font-size: 2rem; font-family: 'JetBrains Mono', monospace; font-weight: 800; margin: 6px 0; color: #fff; }}
    .section {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 14px; padding: 28px; margin-bottom: 32px; }}
    .section-title {{ font-size: 1.3rem; font-weight: 800; color: #fff; margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 12px; }}
    .figure-container {{ background: #090d16; border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin: 20px 0; text-align: center; }}
    .figure-container img {{ max-width: 100%; height: auto; border-radius: 8px; }}
    .figure-caption {{ font-size: 0.85rem; color: var(--text-muted); margin-top: 10px; font-weight: 600; }}
    @media print {{
      body {{ background: #fff !important; color: #1e293b !important; padding: 0; }}
      .action-bar {{ display: none !important; }}
      .header {{ background: #f8fafc !important; border: 1px solid #cbd5e1 !important; color: #000 !important; }}
      .section {{ background: #fff !important; border: 1px solid #e2e8f0 !important; color: #1e293b !important; }}
      .kpi-card {{ background: #f8fafc !important; border: 1px solid #cbd5e1 !important; }}
      .kpi-val {{ color: #0f172a !important; }}
      .figure-container {{ background: #fff !important; border: 1px solid #e2e8f0 !important; }}
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="action-bar">
      <div style="font-size: 0.9rem; font-weight: 600;">ScamOrLegit V3 &bull; Fresh Unseen Benchmark Report</div>
      <button class="print-btn" onclick="window.print()">🖨️ Download / Print PDF</button>
    </div>
    <div class="header">
      <div class="tag">Fresh Unseen Evaluation &bull; N=30</div>
      <h1>Fresh Unseen Benchmark Report</h1>
      <p style="color: #94a3b8;">Out-of-sample empirical evaluation across 15 emerging scam vectors and 15 authentic transactions</p>
    </div>
    <div class="kpi-grid">
      <div class="kpi-card"><div style="font-size: 0.78rem; text-transform: uppercase; color: #9ca3af; font-weight: 700;">Accuracy</div><div class="kpi-val" style="color: #34d399;">96.67%</div><div style="font-size: 0.75rem; color: #9ca3af;">29 / 30 Correct</div></div>
      <div class="kpi-card"><div style="font-size: 0.78rem; text-transform: uppercase; color: #9ca3af; font-weight: 700;">Precision</div><div class="kpi-val" style="color: #38bdf8;">100.00%</div><div style="font-size: 0.75rem; color: #9ca3af;">Zero False Positives</div></div>
      <div class="kpi-card"><div style="font-size: 0.78rem; text-transform: uppercase; color: #9ca3af; font-weight: 700;">Scam Recall</div><div class="kpi-val" style="color: #818cf8;">93.33%</div><div style="font-size: 0.75rem; color: #9ca3af;">14 / 15 Caught</div></div>
      <div class="kpi-card"><div style="font-size: 0.78rem; text-transform: uppercase; color: #9ca3af; font-weight: 700;">V3 Semantic Lift</div><div class="kpi-val" style="color: #f472b6;">+66.67%</div><div style="font-size: 0.75rem; color: #9ca3af;">Over V2 Rule Engine</div></div>
    </div>
    <div class="section">
      <div class="section-title">Section 1: Confusion Matrix & Heuristic Lift</div>
      <div class="figure-container"><img src="{b64_cm}"><div class="figure-caption">Figure 1: Fresh Confusion Matrix (N=30) at Decision Boundary &Theta; = 60.</div></div>
      <div class="figure-container"><img src="{b64_v2v3}"><div class="figure-caption">Figure 2: Threat Detection Recall: V2 Deterministic (26.67%) vs. V3 Semantic Hybrid (93.33%).</div></div>
    </div>
    <div class="section">
      <div class="section-title">Section 2: Category Detection, Score Spread & Fallback Resilience</div>
      <div class="figure-container"><img src="{b64_cat}"><div class="figure-caption">Figure 3: Category-Level Detection Breakdown Across 15 Emerging Vectors.</div></div>
      <div class="figure-container"><img src="{b64_score}"><div class="figure-caption">Figure 4: Risk Score Spread Demonstrating 55-Point Separation.</div></div>
      <div class="figure-container"><img src="{b64_time}"><div class="figure-caption">Figure 5: Timing Profile and Fallback Resilience Audit.</div></div>
    </div>
  </div>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated Fresh HTML at {html_path}")


def generate_adversarial_report():
    artifact_dir = r"C:\Users\Adity\.gemini\antigravity\brain\5be458e5-bb50-4d3c-b4b2-40755c64f1df"
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    # 1. Copy Markdown report
    src_md = os.path.join(artifact_dir, "adversarial_100_benchmark_report.md")
    dst_md = os.path.join(reports_dir, "adversarial_100_benchmark_report.md")
    if os.path.exists(src_md):
        shutil.copyfile(src_md, dst_md)
        print(f"Copied adversarial MD to {dst_md}")

    # Image Paths
    img_cm = os.path.join(artifact_dir, "fig1_adversarial_100_confusion_matrix.png")
    img_v2v3 = os.path.join(artifact_dir, "fig2_adversarial_100_v2_vs_v3_lift.png")
    img_score = os.path.join(artifact_dir, "fig3_adversarial_100_score_distribution.png")
    img_roc = os.path.join(artifact_dir, "fig4_adversarial_100_roc_pr_curves.png")
    img_lat = os.path.join(artifact_dir, "fig5_adversarial_100_latency_profile.png")

    # 2. Build PDF Report
    pdf_path = os.path.join(reports_dir, "adversarial_100_benchmark_report.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=48
    )

    usable_width = 523.27
    styles = getSampleStyleSheet()

    c_primary = colors.HexColor("#1E1B4B")
    c_accent = colors.HexColor("#4F46E5")     # Indigo theme for Adversarial
    c_text = colors.HexColor("#0F172A")
    c_muted = colors.HexColor("#475569")
    c_border = colors.HexColor("#CBD5E1")
    c_bg_light = colors.HexColor("#F8FAFC")

    title_style = ParagraphStyle('DocTitle', fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=c_primary, spaceAfter=6)
    subtitle_style = ParagraphStyle('DocSub', fontName='Helvetica', fontSize=10.5, leading=14, textColor=c_muted, spaceAfter=12)
    h1_style = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=13, leading=17, textColor=c_accent, spaceBefore=14, spaceAfter=8, keepWithNext=True)
    body_style = ParagraphStyle('Body', fontName='Helvetica', fontSize=9, leading=13, textColor=c_text, spaceAfter=6)
    caption_style = ParagraphStyle('Cap', fontName='Helvetica-Oblique', fontSize=8, leading=11, textColor=c_muted, alignment=1, spaceBefore=4, spaceAfter=10)
    th_style = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white, alignment=1)
    tc_style = ParagraphStyle('TC', fontName='Helvetica', fontSize=7.5, leading=10, textColor=c_text)
    tc_bold = ParagraphStyle('TCB', fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=c_text)
    tc_center = ParagraphStyle('TCC', fontName='Helvetica', fontSize=7.5, leading=10, textColor=c_text, alignment=1)

    story = []

    badge = Table([[Paragraph("<font color='#4F46E5'><b>LARGE-SCALE ADVERSARIAL BENCHMARK (N=100) • STRESS TEST VALIDATION</b></font>", tc_style)]], colWidths=[usable_width])
    badge.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EEF2FF")), ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#C7D2FE")), ('PADDING', (0,0), (-1,-1), 4)]))
    story.append(badge)
    story.append(Spacer(1, 6))

    story.append(Paragraph("ScamOrLegit V3: 100-Sample Adversarial Benchmark Report", title_style))
    story.append(Paragraph("Stress-Testing Detection Performance on 50 Evasion Scams and 50 Ambiguous Legitimate Messages", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=0, spaceAfter=8))

    kpis = [
        [
            Paragraph("<b>Overall Accuracy</b><br/><font size='14' color='#4F46E5'><b>84.00%</b></font><br/><font size='6.5' color='#64748B'>84 / 100 Correct</font>", tc_center),
            Paragraph("<b>Precision</b><br/><font size='14' color='#0284C7'><b>86.96%</b></font><br/><font size='6.5' color='#64748B'>40 / 46 Valid Flags</font>", tc_center),
            Paragraph("<b>Scam Recall</b><br/><font size='14' color='#059669'><b>80.00%</b></font><br/><font size='6.5' color='#64748B'>40 / 50 Caught</font>", tc_center),
            Paragraph("<b>Semantic Lift</b><br/><font size='14' color='#D97706'><b>+60.00%</b></font><br/><font size='6.5' color='#64748B'>Over Heuristic V2</font>", tc_center)
        ]
    ]
    t_kpis = Table(kpis, colWidths=[usable_width/4.0]*4)
    t_kpis.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), c_bg_light), ('BOX', (0,0), (-1,-1), 1, c_border), ('INNERGRID', (0,0), (-1,-1), 0.5, c_border), ('PADDING', (0,0), (-1,-1), 6)]))
    story.append(t_kpis)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Section 1: Evaluation Setup & Measured Confusion Matrix", h1_style))
    story.append(Paragraph("Evaluating AI threat detection on 100 edge cases provides statistical confidence. The benchmark pairs 50 evasion-focused scams (soft grooming romance, fake debt settlement, copy-trading traps, typosquatting) against 50 ambiguous legitimate messages (aggressive collection notices, medical portal reports with 48h limit, P2P expense splits).", body_style))

    if os.path.exists(img_cm):
        story.append(Image(img_cm, width=usable_width*0.7, height=210))
        story.append(Paragraph("Figure 1: Adversarial Confusion Matrix (N=100) at Decision Boundary &Theta; = 60 (Accuracy: 84.00%, Precision: 86.96%).", caption_style))

    story.append(Paragraph("Section 2: V2 Deterministic vs. V3 Semantic Hybrid Lift", h1_style))
    story.append(Paragraph("On 50 sophisticated adversarial attacks, the V2 rule engine failed completely, catching only 10 attacks (20.00% recall). The V3 Semantic Hybrid Engine intercepted 40 of 50 attacks, representing a +60.00% semantic lift.", body_style))

    if os.path.exists(img_v2v3):
        story.append(Image(img_v2v3, width=usable_width*0.75, height=200))
        story.append(Paragraph("Figure 2: Adversarial Threat Detection Recall: V2 Deterministic (20.00%) vs. V3 Semantic Hybrid (80.00%).", caption_style))

    story.append(PageBreak())

    story.append(Paragraph("Section 3: Score Separation, ROC/PR Curves & Latency Profile", h1_style))
    if os.path.exists(img_score):
        story.append(Image(img_score, width=usable_width, height=200))
        story.append(Paragraph("Figure 3: Bimodal Risk Score Separation Across 100 Adversarial Cases.", caption_style))

    if os.path.exists(img_roc):
        story.append(Image(img_roc, width=usable_width, height=200))
        story.append(Paragraph("Figure 4: Receiver Operating Characteristic (ROC) and Precision-Recall (PR) Curves for N=100.", caption_style))

    if os.path.exists(img_lat):
        story.append(Image(img_lat, width=usable_width*0.75, height=190))
        story.append(Paragraph("Figure 5: Mean Latency Attribution: Local Heuristics & ChromaDB RAG (385 ms) vs. Foundation LLM (4,420 ms).", caption_style))

    doc.build(story, canvasmaker=lambda *args, **kwargs: NumberedCanvas("ScamOrLegit V3 — 100-Sample Adversarial Benchmark Report (N=100)", *args, **kwargs))
    print(f"Generated Adversarial PDF at {pdf_path}")

    # 3. Build Standalone HTML Report
    b64_cm = b64_img(img_cm)
    b64_v2v3 = b64_img(img_v2v3)
    b64_score = b64_img(img_score)
    b64_roc = b64_img(img_roc)
    b64_lat = b64_img(img_lat)

    html_path = os.path.join(reports_dir, "adversarial_100_benchmark_report.html")
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Adversarial 100 Benchmark Report (N=100) | ScamOrLegit V3</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{ --bg-primary: #0a0e17; --bg-surface: #111827; --border: #374151; --text-main: #f9fafb; --text-muted: #9ca3af; --indigo: #6366f1; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg-primary); color: var(--text-main); font-family: 'Inter', sans-serif; line-height: 1.6; padding: 32px 20px; }}
    .wrapper {{ max-width: 1000px; margin: 0 auto; }}
    .action-bar {{ display: flex; justify-content: space-between; align-items: center; background: rgba(17, 24, 39, 0.8); border: 1px solid var(--border); padding: 12px 20px; border-radius: 12px; margin-bottom: 24px; position: sticky; top: 12px; z-index: 100; backdrop-filter: blur(10px); }}
    .print-btn {{ background: linear-gradient(135deg, #6366f1, #4f46e5); border: none; color: #fff; font-weight: 700; font-size: 0.85rem; padding: 10px 20px; border-radius: 8px; cursor: pointer; }}
    .header {{ background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%); border: 1px solid rgba(99, 102, 241, 0.4); border-radius: 16px; padding: 36px; margin-bottom: 32px; }}
    .tag {{ display: inline-block; background: rgba(99, 102, 241, 0.2); border: 1px solid #6366f1; color: #c7d2fe; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; padding: 4px 12px; border-radius: 999px; margin-bottom: 12px; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; color: #fff; margin-bottom: 8px; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px; }}
    .kpi-card {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: center; }}
    .kpi-val {{ font-size: 2rem; font-family: 'JetBrains Mono', monospace; font-weight: 800; margin: 6px 0; color: #fff; }}
    .section {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 14px; padding: 28px; margin-bottom: 32px; }}
    .section-title {{ font-size: 1.3rem; font-weight: 800; color: #fff; margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 12px; }}
    .figure-container {{ background: #090d16; border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin: 20px 0; text-align: center; }}
    .figure-container img {{ max-width: 100%; height: auto; border-radius: 8px; }}
    .figure-caption {{ font-size: 0.85rem; color: var(--text-muted); margin-top: 10px; font-weight: 600; }}
    @media print {{
      body {{ background: #fff !important; color: #1e293b !important; padding: 0; }}
      .action-bar {{ display: none !important; }}
      .header {{ background: #f8fafc !important; border: 1px solid #cbd5e1 !important; color: #000 !important; }}
      .section {{ background: #fff !important; border: 1px solid #e2e8f0 !important; color: #1e293b !important; }}
      .kpi-card {{ background: #f8fafc !important; border: 1px solid #cbd5e1 !important; }}
      .kpi-val {{ color: #0f172a !important; }}
      .figure-container {{ background: #fff !important; border: 1px solid #e2e8f0 !important; }}
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="action-bar">
      <div style="font-size: 0.9rem; font-weight: 600;">ScamOrLegit V3 &bull; 100-Sample Adversarial Benchmark Report</div>
      <button class="print-btn" onclick="window.print()">🖨️ Download / Print PDF</button>
    </div>
    <div class="header">
      <div class="tag">Adversarial Evaluation &bull; N=100</div>
      <h1>Adversarial 100 Benchmark Report</h1>
      <p style="color: #94a3b8;">Stress-testing detection performance on 50 evasion scams and 50 ambiguous legitimate messages</p>
    </div>
    <div class="kpi-grid">
      <div class="kpi-card"><div style="font-size: 0.78rem; text-transform: uppercase; color: #9ca3af; font-weight: 700;">Accuracy</div><div class="kpi-val" style="color: #818cf8;">84.00%</div><div style="font-size: 0.75rem; color: #9ca3af;">84 / 100 Correct</div></div>
      <div class="kpi-card"><div style="font-size: 0.78rem; text-transform: uppercase; color: #9ca3af; font-weight: 700;">Precision</div><div class="kpi-val" style="color: #38bdf8;">86.96%</div><div style="font-size: 0.75rem; color: #9ca3af;">40 / 46 Valid Flags</div></div>
      <div class="kpi-card"><div style="font-size: 0.78rem; text-transform: uppercase; color: #9ca3af; font-weight: 700;">Scam Recall</div><div class="kpi-val" style="color: #34d399;">80.00%</div><div style="font-size: 0.75rem; color: #9ca3af;">40 / 50 Caught</div></div>
      <div class="kpi-card"><div style="font-size: 0.78rem; text-transform: uppercase; color: #9ca3af; font-weight: 700;">V3 Semantic Lift</div><div class="kpi-val" style="color: #f472b6;">+60.00%</div><div style="font-size: 0.75rem; color: #9ca3af;">Over V2 Rule Engine</div></div>
    </div>
    <div class="section">
      <div class="section-title">Section 1: Confusion Matrix & Heuristic Lift</div>
      <div class="figure-container"><img src="{b64_cm}"><div class="figure-caption">Figure 1: Adversarial Confusion Matrix (N=100) at Decision Boundary &Theta; = 60.</div></div>
      <div class="figure-container"><img src="{b64_v2v3}"><div class="figure-caption">Figure 2: Threat Detection Recall: V2 Deterministic (20.00%) vs. V3 Semantic Hybrid (80.00%).</div></div>
    </div>
    <div class="section">
      <div class="section-title">Section 2: Score Distribution, ROC/PR Curves & Latency</div>
      <div class="figure-container"><img src="{b64_score}"><div class="figure-caption">Figure 3: Bimodal Risk Score Separation Across 100 Adversarial Cases.</div></div>
      <div class="figure-container"><img src="{b64_roc}"><div class="figure-caption">Figure 4: Receiver Operating Characteristic (ROC) and Precision-Recall (PR) Curves for N=100.</div></div>
      <div class="figure-container"><img src="{b64_lat}"><div class="figure-caption">Figure 5: Mean Latency Attribution Profile.</div></div>
    </div>
  </div>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated Adversarial HTML at {html_path}")


if __name__ == "__main__":
    generate_fresh_report()
    generate_adversarial_report()
