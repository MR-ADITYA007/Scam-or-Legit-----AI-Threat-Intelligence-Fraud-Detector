"""
Authoritative Risk Engine and Threshold Classification Module for ScamOrLegit.
Centralizes risk scoring thresholds, indicator canonicalization, deduplication,
and evidence-based heuristic scoring.
"""

import re
from typing import Dict, Any, List
from urllib.parse import urlparse

# Authoritative Risk Thresholds:
# 0–24: Low Risk
# 25–59: Caution
# 60–84: High Scam Risk
# 85–100: Critical Threat

RISK_THRESHOLDS = [
    (0, 24, "Low Risk", "#10b981", "rgba(16, 185, 129, 0.16)"),
    (25, 59, "Caution", "#f59e0b", "rgba(245, 158, 11, 0.16)"),
    (60, 84, "High Scam Risk", "#f97316", "rgba(249, 115, 22, 0.16)"),
    (85, 100, "Critical Threat", "#f43f5e", "rgba(244, 63, 94, 0.16)")
]

TRUSTED_DOMAINS = {
    "amazon.com", "google.com", "paypal.com", "chase.com", "usps.com",
    "microsoft.com", "apple.com", "ups.com", "fedex.com", "bankofamerica.com",
    "wellsfargo.com", "citi.com", "capitalone.com", "netflix.com", "linkedin.com",
    "github.com", "zoom.us", "slack.com", "dhl.com", "spotify.com", "uber.com",
    "duolingo.com", "coursera.org", "docusign.com", "venmo.com", "zellepay.com",
    "amazon.jobs", "target.com", "doordash.com", "dropbox.com", "lyft.com"
}

CANONICAL_CATEGORIES = {
    "impersonation": "Brand or Authority Impersonation",
    "urgency_or_coercion": "Artificial Urgency & Threat Tactics",
    "credential_theft": "Credential Harvesting / OTP Theft",
    "suspicious_link": "Deceptive or Unverified Link",
    "payment_manipulation": "Untraceable / Peer-to-Peer Payment Demand",
    "advance_fee": "Upfront Fee / Registration Deposit Trap",
    "gift_card_request": "Gift Card Payment Request",
    "suspicious_investment_claim": "Guaranteed Profit / High-Yield Claim",
    "malware_indicator": "Suspicious Attachment or Software Request",
    "account_takeover": "Account Security Alert Hijack",
    "identity_information_request": "Sensitive Personal Info Demand"
}


def classify_risk_level(score: int) -> Dict[str, Any]:
    """
    Authoritative classification function. Maps a score (0-100) to its exact risk level and color tokens.
    """
    score = max(0, min(100, int(round(score))))
    for min_val, max_val, label, color, bg_style in RISK_THRESHOLDS:
        if min_val <= score <= max_val:
            return {
                "score": score,
                "level": label,
                "color": color,
                "bg_style": bg_style,
                "disclaimer": "Heuristic risk score based on pattern matching and indicator analysis, not a statistical probability of fraud."
            }
    return {
        "score": score,
        "level": "Critical Threat" if score >= 85 else "High Scam Risk" if score >= 60 else "Caution" if score >= 25 else "Low Risk",
        "color": "#f43f5e" if score >= 85 else "#f97316" if score >= 60 else "#f59e0b" if score >= 25 else "#10b981",
        "bg_style": "rgba(244, 63, 94, 0.16)",
        "disclaimer": "Heuristic risk score based on pattern matching and indicator analysis."
    }


class DeterministicRiskEngine:
    def __init__(self):
        pass

    def extract_indicators(self, text: str) -> List[Dict[str, Any]]:
        text_lower = text.lower()
        findings = []

        # 0. Check URLs in content
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text)
        untrusted_urls = []
        if urls:
            for u in urls:
                try:
                    target = u if u.startswith("http") else "http://" + u
                    host = urlparse(target).netloc.lower()
                    if ":" in host:
                        host = host.split(":")[0]
                    is_trusted = any(host == t or host.endswith("." + t) for t in TRUSTED_DOMAINS)
                    if not is_trusted:
                        untrusted_urls.append((u, host))
                except Exception:
                    untrusted_urls.append((u, u))

        # 1. OTP & Credential Harvesting (Distinguish Informational 2FA vs Theft Request)
        if any(k in text_lower for k in ["otp", "verification code", "security code", "2fa code"]):
            # Negative warnings guarding legitimate 2FA notices
            has_do_not_share = any(neg in text_lower for neg in ["do not share", "never share", "don't share", "do not give", "don't give"])
            
            disclose_prompts = [
                "call support", "state code", "provide this code", "provide code", "give this code",
                "tell our", "enter code at", "verify at http", "customer care executive", "support officer",
                "reply with the 6-digit", "reply with the code", "share this code with"
            ]

            if (not has_do_not_share and any(p in text_lower for p in disclose_prompts)) or untrusted_urls:
                findings.append({
                    "canonical_category": "credential_theft",
                    "severity": "Critical",
                    "description": "Requests disclosure of 2FA/OTP code to caller, support representative, or unverified URL.",
                    "matched_evidence": "OTP code disclosure request detected.",
                    "weight": 60
                })

        # 2. Bank Security Alert / Account Restriction + Link
        bank_names = ["chase", "bank of america", "wells fargo", "citibank", "citi", "capital one", "sbi", "hdbc", "barclays"]
        alert_words = ["locked", "suspended", "unauthorized", "suspicious activity", "suspicious login", "card was blocked", "deactivated", "restore access", "reactivate", "security alert", "security warning"]
        if (any(b in text_lower for b in bank_names) and any(a in text_lower for a in alert_words)) or ("security warning" in text_lower and "account" in text_lower) or ("security alert" in text_lower and "access" in text_lower):
            if untrusted_urls or "verify at" in text_lower or "unblock" in text_lower:
                findings.append({
                    "canonical_category": "account_takeover",
                    "severity": "Critical",
                    "description": "Claims account restriction or security alert with unverified authentication link.",
                    "matched_evidence": "Bank security alert with unverified verification link.",
                    "weight": 60
                })

        # 3. UPI / Peer-to-Peer Reverse PIN Trap
        if any(k in text_lower for k in ["upi", "phonepe", "gpay", "paytm"]):
            if any(p in text_lower for p in ["4-digit", "secret pin", "enter your pin", "input your secret pin", "enter pin", "input your pin", "scan qr", "scan this qr"]):
                if any(r in text_lower for r in ["receive", "claim", "cashback", "deposit money", "buyer sent"]):
                    findings.append({
                        "canonical_category": "payment_manipulation",
                        "severity": "Critical",
                        "description": "Instructs to enter UPI PIN or scan QR code to receive/claim incoming money (Reverse PIN Trap).",
                        "matched_evidence": "UPI PIN reverse money transfer pattern.",
                        "weight": 60
                    })

        # 4. Check Overpayment Scam (Fake Job / Remote Work)
        if re.search(r"cashier'?s?\s*check|cashier'?s?\s*cheque|deposit\s*check|mail\s*check|send\s*check", text_lower):
            if any(p in text_lower for p in ["wire", "zelle", "venmo", "supplier", "vendor", "equipment", "keep $", "send $", "return remaining", "bonus"]):
                findings.append({
                    "canonical_category": "payment_manipulation",
                    "severity": "Critical",
                    "description": "Instructs candidate to deposit check and wire/transfer portion back to fake vendor or employer.",
                    "matched_evidence": "Check overpayment fraud scheme detected.",
                    "weight": 60
                })

        # 5. Upfront Fee / Registration / LMS Deposit (Fake Job, Internship & Loan Fraud)
        if any(job in text_lower for job in ["internship", "intern", "remote job", "hired", "data entry", "data specialist", "virtual assistant", "student offer", "remote typist", "loan"]):
            fee_prompts = [
                "training deposit", "refundable deposit", "registration fee", "paper processing fee",
                "activation fee", "stipend deposit", "purchase mandatory", "cyber certificate",
                "lms-certify", "journal processing fee", "publication fee", "processing fee", "registration deposit",
                "collateral insurance fee", "collateral processing fee", "collateral fee"
            ]
            if any(f in text_lower for f in fee_prompts) or (any(pay in text_lower for pay in ["pay $", "pay refundable", "purchase", "deposit $", "transfer $", "send $"]) and any(meth in text_lower for meth in ["zelle", "upi", "crypto", "wire", "lms", "http", "cashapp", "venmo"])):
                findings.append({
                    "canonical_category": "advance_fee",
                    "severity": "Critical",
                    "description": "Requires applicant/borrower to pay upfront deposit, collateral, registration fee, or purchase mandatory courses/certificates.",
                    "matched_evidence": "Upfront fee trap detected.",
                    "weight": 60
                })

        # 6. Advance Fee & Inheritance / Grant / Loan Fraud
        if any(k in text_lower for k in ["inheritance", "lottery", "winner", "grant", "beneficiary", "$1,000,000", "$4.2m", "$850,000", "$2,500,000", "loan approved", "approved for"]):
            if any(f in text_lower for f in ["clearance fee", "attorney fee", "tax clearance", "stamp fee", "processing fee", "transfer fee", "release check", "fund transfer", "collateral", "activation fee"]):
                findings.append({
                    "canonical_category": "advance_fee",
                    "severity": "Critical",
                    "description": "Demands upfront clearance, collateral, attorney, or stamp fee to release inheritance, loan, grant, or lottery funds.",
                    "matched_evidence": "Advance fee fund release trap.",
                    "weight": 60
                })

        # 7. Delivery Carrier Smishing
        if any(c in text_lower for c in ["usps", "fedex", "ups", "dhl", "parcel", "package", "shipment"]):
            delivery_prompts = ["held at customs", "incomplete address", "address error", "redelivery fee", "delivery failed", "delayed", "reschedule delivery"]
            if any(dp in text_lower for dp in delivery_prompts) and untrusted_urls:
                findings.append({
                    "canonical_category": "suspicious_link",
                    "severity": "Critical",
                    "description": "Delivery notification claiming failed delivery, address error, or customs hold with unverified link.",
                    "matched_evidence": "Postal smishing pattern with suspicious link.",
                    "weight": 60
                })

        # 8. Tech Support & Fake Auto-Renewal Invoices
        if any(brand in text_lower for brand in ["geek squad", "mcafee", "norton", "microsoft security", "auto-renewal", "auto-renewed", "subscription of $", "antivirus $"]):
            if any(act in text_lower for act in ["call", "1-800-", "1-888-", "+1-", "technical helpline", "refund department", "refund agent", "cancel charge", "virus detected"]):
                findings.append({
                    "canonical_category": "impersonation",
                    "severity": "Critical",
                    "description": "Fake tech support alert or auto-renewal invoice instructing user to call a toll-free helpline.",
                    "matched_evidence": "Tech support invoice call center trap.",
                    "weight": 60
                })

        # 9. Executive Impersonation (CEO / Director / VP Operations)
        if any(exec_title in text_lower for exec_title in ["ceo", "director", "vp operations", "supervisor"]) and any(act in text_lower for act in ["wire", "gift cards", "gift card", "email codes", "confidential acquisition"]):
            findings.append({
                "canonical_category": "impersonation",
                "severity": "Critical",
                "description": "Impersonates corporate executive or supervisor requesting confidential wire or gift card purchase.",
                "matched_evidence": "Executive impersonation / BEC request.",
                "weight": 60
            })

        # 10. Romance & Overseas Emergency Money Request
        if any(r in text_lower for r in ["deployed officer", "syria", "customs official holding", "gold trunk", "diplomat agent", "my dearest love", "medical emergency clearance"]):
            if any(p in text_lower for p in ["western union", "bitcoin", "crypto", "wire", "transfer $", "send $"]):
                findings.append({
                    "canonical_category": "payment_manipulation",
                    "severity": "Critical",
                    "description": "Emergency fund request from overseas acquaintance requiring wire or cryptocurrency transfer.",
                    "matched_evidence": "Emergency romance / diplomat money transfer request.",
                    "weight": 60
                })

        # 11. Executable Malware Attachments
        if any(ext in text_lower for ext in [".exe", ".scr", ".bat", ".vbs"]):
            if any(act in text_lower for act in ["execute", "run as administrator", "open attached", "download and run", "execute file"]):
                findings.append({
                    "canonical_category": "malware_indicator",
                    "severity": "Critical",
                    "description": "Instructs user to execute binary file attachment (.exe, .scr) on local system.",
                    "matched_evidence": "Executable malware execution prompt.",
                    "weight": 60
                })

        # 12. Gift Card Demands
        if "gift card" in text_lower or "scratch code" in text_lower or "apple card" in text_lower or "steam card" in text_lower:
            if any(k in text_lower for k in ["purchase", "buy", "send", "scratch", "codes", "pins"]):
                findings.append({
                    "canonical_category": "gift_card_request",
                    "severity": "Critical",
                    "description": "Demands purchase of gift cards or submission of scratch-off PIN codes.",
                    "matched_evidence": "Gift card request terms found in message.",
                    "weight": 60
                })

        # 13. Guaranteed Investment Claims
        investment_kws = ["guaranteed", "zero loss", "turn $", "24 hours guaranteed", "high yield", "100% risk free", "giveaway"]
        if any(kw in text_lower for kw in investment_kws) and any(c in text_lower for c in ["crypto", "btc", "usdt", "bot", "trading", "profit"]):
            findings.append({
                "canonical_category": "suspicious_investment_claim",
                "severity": "Critical",
                "description": "Claims guaranteed high financial return or risk-free crypto trading.",
                "matched_evidence": "Investment guarantee claims detected.",
                "weight": 60
            })

        # 14. Standalone Generic Unverified Links
        if untrusted_urls and not findings:
            first_url, first_host = untrusted_urls[0]
            findings.append({
                "canonical_category": "suspicious_link",
                "severity": "High",
                "description": f"Contains unverified web domain ({first_host}) outside official brand channels.",
                "matched_evidence": f"Unverified URL: {first_url}",
                "weight": 35
            })

        # 15. Artificial Urgency & Coercion (Secondary Factor)
        urgency_kws = ["immediately", "within 24 hours", "within 48 hours", "within 6 hours", "within 12 hours", "within 2 hours", "action required", "deactivated", "closes today", "urgent action"]
        matched_urgency = [kw for kw in urgency_kws if kw in text_lower]
        if matched_urgency and not any(f["canonical_category"] == "urgency_or_coercion" for f in findings):
            findings.append({
                "canonical_category": "urgency_or_coercion",
                "severity": "High",
                "description": "Uses artificial time pressure or ultimatum to force fast compliance.",
                "matched_evidence": f"Urgency trigger: '{matched_urgency[0]}'",
                "weight": 20
            })

        # Deduplicate findings by canonical category (keep highest weight)
        deduped = {}
        for f in findings:
            cat = f["canonical_category"]
            if cat not in deduped or f["weight"] > deduped[cat]["weight"]:
                deduped[cat] = f

        return list(deduped.values())

    def calculate_score(self, text: str, rag_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        extracted_indicators = self.extract_indicators(text)
        
        base_score = 5
        score_contributions = []

        # Contribution from direct extracted indicators
        for ind in extracted_indicators:
            w = ind["weight"]
            base_score += w
            cat_name = CANONICAL_CATEGORIES.get(ind["canonical_category"], ind["canonical_category"])
            score_contributions.append({
                "category": cat_name,
                "contribution": f"+{w}",
                "reason": ind["description"]
            })

        # Contribution / Adjustment from RAG Evidence
        scam_matches = [m for m in rag_matches if m.get("label", "scam").lower() == "scam"]
        legit_matches = [m for m in rag_matches if m.get("label", "").lower() in ["legitimate", "legit"]]

        if scam_matches:
            top_scam = scam_matches[0]
            sim = top_scam.get("similarity_score", 0.5)
            if sim >= 0.55:
                rag_points = int(sim * 25)
                base_score += rag_points
                score_contributions.append({
                    "category": "RAG Pattern Resemblance",
                    "contribution": f"+{rag_points}",
                    "reason": f"Matches database pattern '{top_scam.get('title')}' (Similarity: {sim})"
                })

        if legit_matches:
            top_legit = legit_matches[0]
            sim = top_legit.get("similarity_score", 0.5)
            if sim >= 0.70 and not extracted_indicators:
                discount = int(sim * 30)
                base_score = max(2, base_score - discount)
                score_contributions.append({
                    "category": "Legitimate Pattern Alignment",
                    "contribution": f"-{discount}",
                    "reason": f"Strongly aligns with trusted reference '{top_legit.get('title')}'"
                })

        final_score = max(0, min(100, base_score))
        classification = classify_risk_level(final_score)

        red_flags = []
        for ind in extracted_indicators:
            red_flags.append({
                "category": CANONICAL_CATEGORIES.get(ind["canonical_category"], ind["canonical_category"]),
                "description": ind["description"],
                "severity": ind["severity"],
                "evidence_source": "Direct Text Analysis",
                "matched_phrase": ind.get("matched_evidence", "")
            })

        pattern_triggers = [CANONICAL_CATEGORIES.get(ind["canonical_category"], ind["canonical_category"]) for ind in extracted_indicators]

        if not extracted_indicators and not rag_matches:
            uncertainty_rating = "High Uncertainty — No clear patterns or direct indicators detected."
        elif extracted_indicators and legit_matches:
            uncertainty_rating = "Moderate Uncertainty — Conflicting signals detected."
        else:
            uncertainty_rating = "Low Uncertainty — Clear signal alignment."

        safety_steps = []
        if final_score >= 60:
            safety_steps.extend([
                "Do NOT click any links, open attachments, or call phone numbers in the message.",
                "Do NOT pay any upfront fees, deposits, or send cryptocurrency/Zelle funds.",
                "Verify the sender independently using an official website or known phone contact."
            ])
        elif final_score >= 25:
            safety_steps.extend([
                "Exercise caution. Double-check sender identity via official channels before responding.",
                "Never share OTPs, passwords, or personal details."
            ])
        else:
            safety_steps.extend([
                "Message appears clean, but remain cautious online.",
                "Never share credentials or sensitive identification numbers."
            ])

        return {
            "risk_score": final_score,
            "risk_level": classification["level"],
            "color": classification["color"],
            "bg_style": classification["bg_style"],
            "disclaimer": classification["disclaimer"],
            "red_flags": red_flags,
            "pattern_triggers": pattern_triggers,
            "score_breakdown": score_contributions,
            "uncertainty": uncertainty_rating,
            "safety_steps": safety_steps,
            "extracted_indicators": extracted_indicators
        }


risk_engine = DeterministicRiskEngine()
