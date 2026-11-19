import sys
import os
import unittest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from main import app

from unittest.mock import patch

class TestAPIEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        
        # Mock Gemini for all API tests to prevent live requests
        self.patcher = patch('llm_analyzer.ScamLLMAnalyzer._analyze_with_gemini')
        self.mock_gemini = self.patcher.start()
        # Return fallback error so it uses deterministic v2 engine securely
        self.mock_gemini.return_value = {
            "error": True,
            "analysis_metadata": {
                "engine": "Deterministic RAG Risk Engine",
                "gemini_active": False,
                "gemini_success_latency_ms": 0.0,
                "gemini_failed_latency_ms": 100.0,
                "rag_count": 0,
                "fallback_status": "Failed: API Quota Mock"
            }
        }
        
    def tearDown(self):
        self.patcher.stop()

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("vector_db", data)
        self.assertIn("gemini_analyzer", data)
        self.assertIn("optional_laya_classifier", data)

    def test_presets_endpoint(self):
        response = self.client.get("/api/presets")
        self.assertEqual(response.status_code, 200)
        presets = response.json()
        self.assertIsInstance(presets, list)
        self.assertGreaterEqual(len(presets), 5)

    def test_analyze_empty_input(self):
        response = self.client.post("/api/analyze", json={"text": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Please provide text", response.json()["detail"])

    def test_analyze_text_scam(self):
        payload = {
            "text": "SECURITY ALERT: Your Chase online banking access has been locked due to suspicious login attempts. Verify identity within 24 hours at http://chase-security-verify-auth.com"
        }
        response = self.client.post("/api/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("risk_score", data)
        self.assertIn("risk_level", data)
        self.assertGreaterEqual(data["risk_score"], 60)
        self.assertIn(data["risk_level"], ["High Scam Risk", "Critical Threat"])
        self.assertGreaterEqual(len(data["red_flags"]), 1)

    def test_analyze_text_legitimate(self):
        payload = {
            "text": "Amazon.com: Your order #114-9842104-5829104 has shipped via UPS. You can track package status anytime inside your official Amazon account app."
        }
        response = self.client.post("/api/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(data["risk_score"], 24)
        self.assertEqual(data["risk_level"], "Low Risk")

    def test_copy_report_consistency(self):
        payload = {
            "text": "Congratulations Student! You have been selected for a 3-Month Virtual Internship! Pay $150 deposit via Zelle."
        }
        response = self.client.post("/api/analyze", json=payload)
        data = response.json()
        score = data["risk_score"]
        level = data["risk_level"]
        if score >= 85:
            self.assertEqual(level, "Critical Threat")
        elif score >= 60:
            self.assertEqual(level, "High Scam Risk")
        elif score >= 25:
            self.assertEqual(level, "Caution")
        else:
            self.assertEqual(level, "Low Risk")

if __name__ == "__main__":
    unittest.main()
