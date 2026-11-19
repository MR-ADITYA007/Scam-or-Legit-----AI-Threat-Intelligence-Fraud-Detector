import sys
import os
import unittest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from risk_engine import classify_risk_level, DeterministicRiskEngine, risk_engine

class TestRiskEngineScoring(unittest.TestCase):

    def test_boundary_scores(self):
        """Verify exact boundary score classification rules."""
        self.assertEqual(classify_risk_level(0)["level"], "Low Risk")
        self.assertEqual(classify_risk_level(24)["level"], "Low Risk")
        self.assertEqual(classify_risk_level(25)["level"], "Caution")
        self.assertEqual(classify_risk_level(59)["level"], "Caution")
        self.assertEqual(classify_risk_level(60)["level"], "High Scam Risk")
        self.assertEqual(classify_risk_level(78)["level"], "High Scam Risk")
        self.assertEqual(classify_risk_level(84)["level"], "High Scam Risk")
        self.assertEqual(classify_risk_level(85)["level"], "Critical Threat")
        self.assertEqual(classify_risk_level(100)["level"], "Critical Threat")

    def test_otp_theft_vs_informational_2fa(self):
        """Test OTP disclosure request triggers high risk, while informational 2FA stays low risk."""
        engine = DeterministicRiskEngine()
        
        # Informational 2FA -> Low Risk
        info_2fa = "Your Google verification code is 482910. Do not share this code with anyone."
        res_info = engine.calculate_score(info_2fa, [])
        self.assertLessEqual(res_info["risk_score"], 24)
        self.assertEqual(res_info["risk_level"], "Low Risk")

        # Disclosure Request -> High / Critical Risk
        theft_otp = "Your OTP code is 984120. Call support officer now at +1-888-555-0199 and state code to prevent locked account."
        res_theft = engine.calculate_score(theft_otp, [])
        self.assertGreaterEqual(res_theft["risk_score"], 60)

    def test_bank_alert_phishing_vs_genuine_notice(self):
        """Test phishing link triggers high risk, while genuine bank notice stays low risk."""
        engine = DeterministicRiskEngine()

        # Genuine Notice -> Low Risk
        genuine_bank = "Chase Alert: A sign-in to your online account occurred from a new browser. If this was you, no action needed."
        res_gen = engine.calculate_score(genuine_bank, [])
        self.assertLessEqual(res_gen["risk_score"], 24)

        # Phishing Alert -> High / Critical Risk
        phish_bank = "Security Warning: Suspicious activity on Capital One account. Verify at http://capitalone-auth-check.net"
        res_phish = engine.calculate_score(phish_bank, [])
        self.assertGreaterEqual(res_phish["risk_score"], 60)

    def test_delivery_smishing_vs_legitimate_delivery(self):
        """Test postal smishing with fake TLD triggers high risk, while ups.com stays low risk."""
        engine = DeterministicRiskEngine()

        # Legitimate -> Low Risk
        legit_del = "UPS Update: Package 1Z9999999999999999 will be delivered today. Track status at https://www.ups.com/track"
        res_legit = engine.calculate_score(legit_del, [])
        self.assertLessEqual(res_legit["risk_score"], 24)

        # Smishing -> High / Critical Risk
        smish_del = "USPS: Delivery failed due to incomplete address. Update at http://usps-redelivery-notice.info"
        res_smish = engine.calculate_score(smish_del, [])
        self.assertGreaterEqual(res_smish["risk_score"], 60)

    def test_job_check_overpayment_and_fees(self):
        """Test check overpayments and pay-to-work traps trigger high risk."""
        engine = DeterministicRiskEngine()

        # Cheque Overpayment
        job_check = "Hired for Remote Data Specialist at $50/hr! We will mail $3,000 cashier check. Wire $2,500 back for equipment."
        res_job = engine.calculate_score(job_check, [])
        self.assertGreaterEqual(res_job["risk_score"], 60)

        # Registration Fee
        intern_fee = "Accepted for Summer AI Internship! Pay $120 registration deposit via UPI within 4 hours."
        res_intern = engine.calculate_score(intern_fee, [])
        self.assertGreaterEqual(res_intern["risk_score"], 60)

        # Genuine Job Offer -> Low Risk
        genuine_job = "Microsoft Careers: Your formal offer letter is posted on https://careers.microsoft.com"
        res_genuine = engine.calculate_score(genuine_job, [])
        self.assertLessEqual(res_genuine["risk_score"], 24)

    def test_upi_pin_trap_vs_normal_venmo(self):
        """Test reverse PIN trap triggers high risk, while normal Venmo request stays low risk."""
        engine = DeterministicRiskEngine()

        # Normal Venmo Request -> Low Risk
        normal_venmo = "Venmo: Alex requested $15.00 for dinner yesterday."
        res_venmo = engine.calculate_score(normal_venmo, [])
        self.assertLessEqual(res_venmo["risk_score"], 24)

        # UPI Reverse PIN Trap -> High / Critical Risk
        upi_trap = "To receive $150 cashback reward in your UPI account, open link and enter your 4-digit UPI PIN."
        res_trap = engine.calculate_score(upi_trap, [])
        self.assertGreaterEqual(res_trap["risk_score"], 60)

    def test_romance_emergency_wire(self):
        """Test romance emergency wire request triggers high risk."""
        engine = DeterministicRiskEngine()
        text = "Deployed officer needs $1,500 via Western Union for medical emergency clearance to come home to be with you."
        res = engine.calculate_score(text, [])
        self.assertGreaterEqual(res["risk_score"], 60)

    def test_malware_attachment_execution(self):
        """Test executable attachment execution prompt triggers high risk."""
        engine = DeterministicRiskEngine()
        text = "Invoice attached Security_Patch.scr. Execute file on your computer to update system settings."
        res = engine.calculate_score(text, [])
        self.assertGreaterEqual(res["risk_score"], 60)

if __name__ == "__main__":
    unittest.main()
