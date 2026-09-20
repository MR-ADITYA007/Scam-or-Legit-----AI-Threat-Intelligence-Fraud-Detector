import os
import json
import re
import logging
from typing import Dict, Any, List
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("llm_analyzer")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

TRUSTED_DOMAINS = [
    "amazon.com", "google.com", "paypal.com", "chase.com", "usps.com", 
    "microsoft.com", "apple.com", "ups.com", "fedex.com", "bankofamerica.com", 
    "wellsfargo.com", "citi.com", "capitalone.com", "netflix.com"
]

class ScamLLMAnalyzer:
    def __init__(self):
        self.client = None
        self.has_gemini = False
        self._init_gemini()

    def _init_gemini(self):
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            logger.info("No GEMINI_API_KEY found in environment. Analyzer will run in Hybrid RAG Heuristic Mode.")
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            self.has_gemini = True
            logger.info("Successfully initialized Gemini Flash Client.")
        except Exception as e:
            logger.warning(f"Could not initialize Google GenAI SDK: {e}. Falling back to Heuristic RAG mode.")

    def analyze(self, content_text: str, rag_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs RAG context + User submission through Gemini or Heuristic Engine"""
        
        # If Gemini is configured, use Gemini API with RAG context
        if self.has_gemini and self.client:
            try:
                return self._analyze_with_gemini(content_text, rag_context)
            except Exception as e:
                logger.error(f"Gemini API analysis failed: {e}. Falling back to RAG Heuristic engine.")

        # Fallback Heuristic Analysis leveraging RAG evidence
        return self._analyze_heuristic(content_text, rag_context)

    def _analyze_with_gemini(self, content_text: str, rag_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        context_str = json.dumps(rag_context, indent=2)
        
        prompt = f"""
You are "Scam or Legit?", an expert AI Fraud Analyst and Cybersecurity Detective.
Analyze the following submitted message, email, job offer, or text for potential scam, phishing, or fraud indicators.

[RETRIEVED VECTOR DATABASE SCAM EVIDENCE]
{context_str}

[USER SUBMISSION TO ANALYZE]
\"\"\"
{content_text}
\"\"\"

INSTRUCTIONS:
Evaluate urgency, financial demands, unverified links, impersonation tactics, grammatical irregularities, and inconsistencies.
Use the retrieved scam evidence as reference patterns.

Return ONLY a valid, single JSON object adhering strictly to this JSON format:
{{
  "risk_score": <integer from 0 to 100>,
  "risk_level": "<Safe | Caution | High Scam Risk | Critical Threat>",
  "scam_category": "<Category name like Phishing, Remote Job Scam, Fake Internship & Education Scam, Smishing, Crypto Fraud, Executive Impersonation, Legitimate>",
  "summary": "<1-2 sentence executive explanation of the finding>",
  "red_flags": [
    {{
      "category": "<Category name>",
      "description": "<Specific red flag explanation>",
      "severity": "<Critical | High | Medium>"
    }}
  ],
  "retrieved_evidence": [
    "<Citation of matched pattern from database>"
  ],
  "linguistic_cues": [
    "<Detected indicator like Artificial Urgency, Peer-to-Peer Transfer Demand, Unofficial Domain>"
  ],
  "recommended_actions": [
    "<Clear step-by-step action for the user to stay safe>"
  ]
}}
"""
        response = self.client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'temperature': 0.2
            }
        )
        
        parsed = json.loads(response.text)
        return parsed

    def _analyze_heuristic(self, content_text: str, rag_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Engineered heuristic analyzer combining vector database similarity with rule-based detection"""
        text_lower = content_text.lower()
        
        red_flags = []
        linguistic_cues = []
        score = 5
        
        # 1. Financial & Payment Triggers
        payment_kws = ["gift card", "zelle", "cashapp", "venmo", "western union", "wire transfer", "bitcoin", "usdt", "crypto", "cashier's check", "cashier's cheque", "money order", "upi"]
        if any(kw in text_lower for kw in payment_kws):
            score += 35
            red_flags.append({
                "category": "Untraceable Payment Request",
                "description": "Requests non-refundable or peer-to-peer payment (Gift cards, Zelle, Crypto, Wire Transfer, UPI, Cashier Check).",
                "severity": "Critical"
            })
            linguistic_cues.append("Peer-to-Peer Payment Demand")

        # 2. Urgency & Threat Triggers
        urgency_kws = ["immediately", "24 hours", "48 hours", "6 hours", "suspended", "permanently locked", "locked", "urgent", "unauthorized", "legal action", "arrest", "act now", "action required", "verify identity", "security alert", "deactivated", "restricted", "expire", "closes today"]
        if any(kw in text_lower for kw in urgency_kws):
            score += 25
            red_flags.append({
                "category": "Artificial Urgency & Threat Tactics",
                "description": "Uses artificial deadline, account suspension warning, or threat of penalty to force immediate action.",
                "severity": "High"
            })
            linguistic_cues.append("Artificial Urgency Spike")

        # 3. Job & Cheque Overpayment Scams
        job_kws = ["cashier's cheque", "deposit the check", "equipment supplier", "sign-on bonus", "interview via telegram", "data entry remote", "keep $", "wire remaining"]
        if any(kw in text_lower for kw in job_kws):
            score += 35
            red_flags.append({
                "category": "Overpayment / Check Fraud",
                "description": "Instructs to deposit a check and transfer remaining funds back to an unverified vendor or recruiter.",
                "severity": "Critical"
            })
            linguistic_cues.append("Check Overpayment Pattern")

        # 3b. Fake Internship & Educational Fees Scams
        internship_kws = [
            "internship", "virtual internship", "training fee", "registration fee", 
            "stipend security deposit", "refundable deposit", "pay to reserve", 
            "offer letter attached", "lms-certify", "mandatory certificate", "student offer",
            "candidate slot", "stipend account", "task completion", "paper processing fee",
            "publication fee", "student intern"
        ]
        if any(kw in text_lower for kw in internship_kws) and any(fee_kw in text_lower for fee_kw in ["fee", "deposit", "pay", "zelle", "upi", "purchase", "$", "lms", "crypto"]):
            score += 40
            red_flags.append({
                "category": "Pay-To-Work Internship Trap",
                "description": "Requires candidate/student to pay upfront registration, security deposit, training fee, or purchase mandatory courses to secure an internship.",
                "severity": "Critical"
            })
            linguistic_cues.append("Student Exploitation Pattern")
            linguistic_cues.append("Upfront Fee Demand")

        # 4. Link & Domain Analysis (Precise Hostname Parsing)
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content_text)
        if urls:
            suspicious_urls = []
            for u in urls:
                try:
                    target_url = u if u.startswith("http") else "http://" + u
                    parsed = urlparse(target_url)
                    hostname = parsed.netloc.lower()
                    # Strip port if present
                    if ":" in hostname:
                        hostname = hostname.split(":")[0]
                    
                    is_trusted = any(hostname == t or hostname.endswith("." + t) for t in TRUSTED_DOMAINS)
                    if not is_trusted:
                        suspicious_urls.append((u, hostname))
                except Exception:
                    suspicious_urls.append((u, u))

            if suspicious_urls:
                first_url, first_host = suspicious_urls[0]
                score += 30
                red_flags.append({
                    "category": "Suspicious External Link",
                    "description": f"Contains unverified web domain ({first_host}) outside official brand channels.",
                    "severity": "High"
                })
                linguistic_cues.append("Domain Spoofing Risk")

        # 5. RAG Vector Evidence Correlation
        evidence_list = []
        top_match_category = "General Analysis"
        if rag_context:
            best_match = rag_context[0]
            sim = best_match.get("similarity_score", 0.7)
            top_match_category = best_match.get("category", "Pattern Match")
            
            if "legit" not in best_match.get("id", "").lower():
                score += int(sim * 25)
                evidence_list.append(f"Matched Database Pattern: {best_match.get('title')} ({best_match.get('category')})")
                for tactic in best_match.get("tactics", []):
                    if tactic not in linguistic_cues:
                        linguistic_cues.append(tactic)
            else:
                score = max(0, score - 30)
                evidence_list.append(f"Matched Trusted Reference: {best_match.get('title')}")

        # Cap score between 0 and 99
        risk_score = min(99, max(2, score))
        
        # Risk classification
        if risk_score >= 75:
            risk_level = "Critical Threat"
            category = top_match_category if top_match_category != "General Analysis" else "High Risk Fraud"
            summary = "This content exhibits severe red flags including high-risk payment demands, artificial urgency, or matched phishing patterns."
        elif risk_score >= 45:
            risk_level = "High Scam Risk"
            category = top_match_category
            summary = "Multiple suspicious indicators detected. Exercise extreme caution before responding or sharing details."
        elif risk_score >= 20:
            risk_level = "Caution"
            category = "Unverified Communication"
            summary = "Some minor suspicious elements found. Double-check sender identity through official channels."
        else:
            risk_level = "Safe"
            category = "Legitimate Communication"
            summary = "No prominent scam patterns or malicious triggers detected. Standard informational communication."

        # Recommendations
        if risk_score > 30:
            actions = [
                "Do NOT click any embedded links or open attachments.",
                "Do NOT transfer funds, share gift card codes, or send 2FA security codes.",
                "Verify the sender by navigating to the official website directly (do not use phone numbers in the message)."
            ]
        else:
            actions = [
                "Message appears clean, but always remain vigilant online.",
                "Never share passwords or personal identification details."
            ]

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "scam_category": category,
            "summary": summary,
            "red_flags": red_flags if red_flags else [{
                "category": "Clean Signals",
                "description": "No urgent threats, untraceable payment demands, or deceptive links detected.",
                "severity": "Medium"
            }],
            "retrieved_evidence": evidence_list,
            "linguistic_cues": linguistic_cues,
            "recommended_actions": actions
        }

analyzer = ScamLLMAnalyzer()

