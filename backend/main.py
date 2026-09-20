import os
import sys
import base64
import logging
import mimetypes
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main_server")

app = FastAPI(
    title="Scam or Legit? — AI Suspicion Analyzer API",
    description="Vector RAG + Gemini Powered Scam Detection Engine",
    version="1.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    text: str
    image_base64: Optional[str] = None

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "vector_db_count": len(rag_engine.items),
        "use_chroma": rag_engine.use_chroma,
        "llm_gemini_active": analyzer.has_gemini
    }

@app.get("/api/presets")
def get_presets():
    return [
        {
            "id": "preset_bank_sms",
            "name": "🚨 Bank Account Suspension SMS",
            "type": "Phishing SMS",
            "content": "SECURITY ALERT: Your Chase online access is locked due to unusual activity. Verify identity within 24 hours at http://chase-security-verify-auth.com or account will be closed."
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
            "name": "📈 Guaranteed Crypto Trading Bot",
            "type": "Crypto Fraud",
            "content": "Turn $200 into $5,000 in 24 hours guaranteed! Join our VIP Telegram Signal group. Our AI trading bot has zero loss history. Send USDT (TRC-20) to T9xZ8842... now!"
        },
        {
            "id": "preset_legit_amazon",
            "name": "✅ Official Amazon Shipping Alert",
            "type": "Legitimate",
            "content": "Amazon.com: Your order #114-9842104-5829104 has shipped via UPS. You can track package status anytime inside your official Amazon account app."
        }
    ]

@app.post("/api/analyze")
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

    # 2. Process File Upload (if image uploaded)
    if file:
        try:
            contents = await file.read()
            # Simple OCR / Pillow fallback check
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(contents))
            
            # Use basic OCR or fallback placeholder if pytesseract not installed
            try:
                import pytesseract
                ocr_text = pytesseract.image_to_string(image)
                if ocr_text.strip():
                    extracted_text += f"\n[Extracted Text from Image Screenshot]:\n{ocr_text}"
            except Exception:
                extracted_text += f"\n[Uploaded Screenshot Image: {file.filename} (Format: {image.format}, Size: {image.size})]"
        except Exception as e:
            logger.warning(f"Image processing note: {e}")
            if not extracted_text:
                extracted_text = f"Uploaded image file: {file.filename}"

    if not extracted_text or not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Please provide text or upload a screenshot message to analyze.")

    # 3. Retrieve RAG context from ChromaDB
    rag_matches = rag_engine.retrieve_context(extracted_text, top_k=3)

    # 4. LLM / Heuristic Analysis
    analysis_result = analyzer.analyze(extracted_text, rag_matches)
    
    # Attach input preview
    analysis_result["analyzed_input"] = extracted_text[:300] + ("..." if len(extracted_text) > 300 else "")
    
    return analysis_result

# Serve Frontend static directory directly at root
frontend_dir = os.path.abspath(os.path.join(backend_dir, "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

