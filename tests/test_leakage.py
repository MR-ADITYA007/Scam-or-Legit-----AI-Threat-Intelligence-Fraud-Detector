import sys
import os
import json
import unittest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from risk_engine import risk_engine
from rag_engine import rag_engine

class TestDataSeparationAndLeakage(unittest.TestCase):

    def test_heldout_sample_ids_not_in_backend(self):
        """Verify that no held-out sample IDs appear in backend risk engine or knowledge base."""
        heldout_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "eval", "heldout_dataset.json"))
        self.assertTrue(os.path.exists(heldout_path), f"Heldout dataset missing at {heldout_path}")
        
        with open(heldout_path, "r", encoding="utf-8") as f:
            heldout = json.load(f)

        heldout_ids = {item["id"] for item in heldout}

        # Check knowledge base item IDs
        kb_ids = {item["id"] for item in rag_engine.items}
        intersection = heldout_ids.intersection(kb_ids)
        self.assertEqual(len(intersection), 0, f"Found leaked held-out sample IDs in knowledge base: {intersection}")

    def test_heldout_scam_texts_not_in_knowledge_base(self):
        """Verify that zero held-out scam pattern texts are indexed in ChromaDB knowledge base."""
        heldout_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "eval", "heldout_dataset.json"))
        with open(heldout_path, "r", encoding="utf-8") as f:
            heldout = json.load(f)

        scam_heldout_texts = {item["text"].strip().lower() for item in heldout if item.get("label") == "scam"}
        kb_texts = {item["pattern_text"].strip().lower() for item in rag_engine.items}

        leaked_scams = scam_heldout_texts.intersection(kb_texts)
        self.assertEqual(len(leaked_scams), 0, f"Found leaked held-out scam texts in knowledge base: {leaked_scams}")

    def test_risk_engine_source_code_has_no_hardcoded_eval_ids(self):
        """Verify that risk_engine.py source code contains no hardcoded evaluation sample IDs or text literals."""
        risk_engine_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "risk_engine.py"))
        with open(risk_engine_path, "r", encoding="utf-8") as f:
            code = f.read()

        self.assertNotIn("heldout_", code)
        self.assertNotIn("eval_scam_", code)
        self.assertNotIn("eval_legit_", code)

if __name__ == "__main__":
    unittest.main()
