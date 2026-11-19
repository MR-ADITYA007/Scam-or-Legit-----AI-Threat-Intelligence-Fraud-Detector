import os
import sys
import base64
import logging
import mimetypes
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Ensure proper MIME types on Windows platforms
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('image/svg+xml', '.svg')

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from rag_engine import rag_engine
from llm_analyzer import analyzer
from laya_classifier import laya_classifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main_server")

app = FastAPI(
    title="Scam or Legit? — AI Threat Intelligence & Fraud Detector API",
    description="Evidence-Based Vector RAG + Deterministic Risk Engine + Gemini 2.0 Flash Stack",
    version="2.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB upload limit

class AnalyzeRequest(BaseModel):
    text: Optional[str] = Field(None, description="Text message, email body, or job offer content")
    image_base64: Optional[str] = Field(None, description="Optional base64 encoded image screenshot")

class RedFlagItem(BaseModel):
    category: str
    description: str
    severity: str
    evidence_source: Optional[str] = "Direct Text Analysis"
    matched_phrase: Optional[str] = ""

class RAGMatchItem(BaseModel):
    id: str
    title: str
    category: str
    label: str
    similarity_score: float
    source_name: str
    source_url: Optional[str] = ""
    example_type: str

class ScoreBreakdownItem(BaseModel):
    category: str
    contribution: str
    reason: str

class AnalyzeResponse(BaseModel):
    risk_score: int
    risk_level: str
    color: str
    bg_style: str
    disclaimer: str
    scam_category: str
    summary: str
    uncertainty: str
    red_flags: List[RedFlagItem]
    pattern_triggers: List[str]
    rag_matches: List[RAGMatchItem]
    score_breakdown: List[ScoreBreakdownItem]
    safety_steps: List[str]
    analyzed_input: str
    analysis_metadata: Dict[str, Any]

@app.get("/api/health")
def health_check():
    """Returns component health status without exposing sensitive environment variables or keys."""
    return {
        "status": "online",
        "api_version": "2.0.0",
        "vector_db": {
            "item_count": len(rag_engine.items),
            "chroma_active": rag_engine.use_chroma
        },
        "gemini_analyzer": {
            "active": analyzer.has_gemini,
            "model": os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")
        },
        "optional_laya_classifier": {
            "enabled": laya_classifier.enabled,
            "status": "active" if laya_classifier.enabled else "disabled (optional)"
        },
        "ocr_engine": {
            "available": True
        }
    }

@app.get("/api/presets")
def get_presets():
    """Returns sample test messages including scams, subtle traps, and legitimate communications."""
    return [
        {
            "id": "preset_bank_sms",
            "name": "🚨 Bank Account Lock Phishing SMS",
            "type": "Phishing SMS",
            "content": "SECURITY ALERT: Your Chase online banking access has been locked due to suspicious login attempts. Verify identity within 24 hours at http://chase-security-verify-auth.com or account will be closed."
        },
        {
            "id": "preset_fake_internship",
            "name": "🎓 Fake Internship Deposit Scam",
            "type": "Fake Internship Scam",
            "content": "Congratulations Student! You have been selected for a 3-Month Remote AI & Web Development Virtual Internship at FutureTech Innovations! Offer Letter is attached. To reserve your candidate slot and issue your employee ID, pay a refundable training & stipend deposit of $150 via Zelle / UPI within 6 hours."
        },
        {
            "id": "preset_remote_job",
            "name": "💼 Remote Data Entry Cheque Scam",
            "type": "Fake Job Offer",
            "content": "Congratulations! You are hired for Remote Data Specialist at $45/hr. We will send a $3,500 cashier's check for equipment. Deposit check, keep $500 bonus, and wire $3,000 to our equipment vendor via Zelle."
        },
        {
            "id": "preset_crypto_vip",
            "name": "📈 Guaranteed Crypto Bot Scam",
            "type": "Crypto Fraud",
            "content": "Turn $200 into $5,000 in 24 hours guaranteed! Join our VIP Telegram Signal group. Our AI trading bot has zero loss history. Send USDT (TRC-20) to T9xZ8842... now!"
        },
        {
            "id": "preset_legit_amazon",
            "name": "✅ Official Amazon Shipping Receipt",
            "type": "Legitimate",
            "content": "Amazon.com: Your order #114-9842104-5829104 has shipped via UPS. You can track package status anytime inside your official Amazon account app."
        }
    ]

@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_submission(
    request: Request,
    payload: Optional[AnalyzeRequest] = None,
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    extracted_text = ""
    
    # 1. Parse JSON body if available
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()
            extracted_text = data.get("text", "")
        elif payload and payload.text:
            extracted_text = payload.text
        elif text:
            extracted_text = text
    except Exception as e:
        logger.warning(f"Body parsing note: {e}")
        if text:
            extracted_text = text

    # 2. Process Image File Upload / Screenshot OCR if provided
    if file:
        try:
            contents = await file.read()
            if len(contents) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(status_code=400, detail="Uploaded file exceeds 5MB size limit.")
                
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(contents))
            
            ocr_text = ""
            try:
                import pytesseract
                ocr_text = pytesseract.image_to_string(image).strip()
            except Exception:
                logger.info("pytesseract not installed or tesseract binary unavailable; falling back to OCR image info.")

            if ocr_text:
                extracted_text = (extracted_text + "\n" + f"[Extracted OCR Text from Screenshot]:\n{ocr_text}").strip()
            else:
                extracted_text = (extracted_text + "\n" + f"[Uploaded Screenshot Image: {file.filename} (Format: {image.format}, Size: {image.size})]").strip()
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Image processing note: {e}")
            if not extracted_text:
                extracted_text = f"Uploaded image file: {file.filename}"

    if not extracted_text or not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Please provide text or upload a screenshot image to analyze.")

    # 3. Retrieve Context from Knowledge Base & ChromaDB
    rag_matches = rag_engine.retrieve_context(extracted_text, top_k=3)

    # 4. Perform Deterministic Risk Engine Scoring & LLM Synthesis
    analysis_result = analyzer.analyze(extracted_text, rag_matches)
    
    # Attach input preview snippet safely
    analysis_result["analyzed_input"] = extracted_text[:300] + ("..." if len(extracted_text) > 300 else "")
    
    return analysis_result

# Serve Frontend static directory directly at root
frontend_dir = os.path.abspath(os.path.join(backend_dir, "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
