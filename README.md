# ScamOrLegit — AI Threat Intelligence & Fraud Detector

An evidence-based AI scam, phishing, and fraud suspicion analyzer powered by a **Deterministic Risk Engine**, **ChromaDB Vector RAG**, and **Google Gemini 2.0 Flash**.

---

## 🚀 Key Features & Architecture

- **Authoritative Risk Classification Engine (`backend/risk_engine.py`)**:
  Centralized thresholds (0–24 Low Risk, 25–59 Caution, 60–84 High Scam Risk, 85–100 Critical Threat). Fixed UI gauge & banner inconsistencies.
- **Hybrid Vector & Keyword RAG (`backend/rag_engine.py`)**:
  Indexes both **documented scam patterns** and **legitimate counterexamples** with source metadata (FTC, FBI IC3, CERT-In, USPIS).
- **Gemini 2.0 Flash Synthesis (`backend/llm_analyzer.py`)**:
  Enriches reports with human-readable executive summaries, evidence citations, and safety guidance without overriding authoritative backend scores.
- **Modular Classifier Abstraction (`backend/classifier_interface.py`, `backend/laya_classifier.py`)**:
  Adapter structure prepared for optional future **LAYA Model** integration (`ENABLE_LAYA=false` by default).
- **OCR Screenshot Input**:
  Supports direct image screenshot analysis alongside raw text input.
- **Modern Dark Visual UI**:
  Neon/purple glassmorphic dashboard with SVG radial threat gauge, red flag cards, RAG evidence list, and one-click security report copying.

---

## 🛠️ Setup & Installation

### 1. Requirements
- Python 3.9+
- Pip dependencies: `fastapi`, `uvicorn`, `pydantic`, `chromadb`, `google-genai`, `python-dotenv`, `pillow`

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory (or use `.env.example`):
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash
ENABLE_LAYA=false
```
*Note: If no Gemini API key is provided, the application automatically runs in standalone local RAG heuristic mode.*

---

## ⚡ Running the Application

Launch the backend server and serve the frontend UI at `http://localhost:8000`:
```bash
python run.py
```
Or run uvicorn directly:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧪 Running Automated Tests

Run the unit test suite verifying threshold boundaries, score consistency (e.g. score 78 = High Scam Risk), indicator deduplication, and API schema contracts:
```bash
python tests/test_risk_engine.py
python tests/test_api.py
```

---

## 📊 Empirical Accuracy & Performance Evaluation

Run the deep evaluation script over the 100-sample dataset (`eval/dataset.json`):
```bash
python eval/run_deep_evaluation.py
```

### Measured Benchmark Metrics (N=100)
- **Confusion Matrix**: `TP=28`, `FP=0`, `TN=50`, `FN=22`
- **Overall Accuracy**: `78.00%` `(28 + 50) / 100`
- **Precision**: `100.00%` `28 / (28 + 0)`
- **Recall (Sensitivity)**: `56.00%` `28 / (28 + 22)`
- **Specificity**: `100.00%` `50 / (50 + 0)`
- **False Positive Rate (FPR)**: `0.00%` `0 / (0 + 50)`
- **F1 Score**: `71.79%`

### Latency Audit
- **Mean Local Pipeline Latency**: `253.19 ms` (p50: `250.34 ms`, p95: `293.36 ms`)
- **ChromaDB Retrieval**: `253.14 ms`
- **Risk Engine Calculation**: `0.05 ms`
- *Note: Latency applies to local deterministic RAG engine. Live Gemini API network requests (~1.2s–2.5s) and Tesseract OCR (~0.5s–1.5s) are additional when enabled.*

### Saved Artifacts
- JSON Predictions & Metrics: [`eval/evaluation_results.json`](file:///c:/Users/Adity/OneDrive/onedrive/Desktop/Scam%20Detector/eval/evaluation_results.json)
- CSV Per-Sample Table: [`eval/evaluation_results.csv`](file:///c:/Users/Adity/OneDrive/onedrive/Desktop/Scam%20Detector/eval/evaluation_results.csv)

---

## 🔮 Optional Future LAYA Integration

To enable the optional LAYA classifier adapter in the future:
1. Install LAYA dependencies in your environment.
2. Set `ENABLE_LAYA=true` in your `.env` file.
3. The application will initialize the `laya_classifier` module during startup. If disabled or missing, it seamlessly falls back to the default Gemini + RAG engine.
