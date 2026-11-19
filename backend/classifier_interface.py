"""
Modular Classifier Interface Abstraction for ScamOrLegit.
Allows plugging in different AI model backends (Gemini, LAYA, local transformer classifiers)
without changing core API contracts or risk engine integration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseScamClassifier(ABC):
    """Abstract base class for Scam/Fraud classification models."""

    @abstractmethod
    def predict(
        self,
        text: str,
        extracted_indicators: List[Dict[str, Any]],
        rag_evidence: List[Dict[str, Any]],
        legitimate_counterexamples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Accepts normalized input structures and returns a standardized classification result:
        {
            "predicted_category": str,
            "decision": str,  # e.g., "scam", "legitimate", "ambiguous"
            "confidence": float,
            "supporting_evidence_ids": List[str],
            "model_name": str,
            "model_version": str,
            "is_active": bool
        }
        """
        pass
