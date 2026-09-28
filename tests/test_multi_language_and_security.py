"""Unit Tests for Enterprise Security Suite and Multi-Language Bridges (Java, COBOL, Fortran, SQL)."""

import unittest
from cobol.cobol_bridge import CobolMainframeEngine, CobolScreeningRecord
from fortran.fortran_bridge import FortranRiskEngine
from security.auth import SecurityAuthManager, UserRole
from security.crypto import EnterpriseCryptoManager, TamperProofAuditLedger
from security.rate_limiter import TokenBucketRateLimiter
from security.sanitizer import SecuritySanitizer


class TestEnterpriseSecuritySuite(unittest.TestCase):
    """Tests AES-256-GCM, HMAC-SHA256, Audit Chaining, Rate Limiting, and Injection Protection."""

    def setUp(self) -> None:
        self.crypto = EnterpriseCryptoManager()
        self.ledger = TamperProofAuditLedger()
        self.limiter = TokenBucketRateLimiter(capacity=3, refill_rate_per_sec=1.0)
        self.auth = SecurityAuthManager()

    def test_aes_gcm_pii_encryption(self) -> None:
        ssn = "999-00-1234"
        encrypted = self.crypto.encrypt_pii(ssn)
        self.assertNotEqual(encrypted, ssn)

        decrypted = self.crypto.decrypt_pii(encrypted)
        self.assertEqual(decrypted, ssn)

    def test_hmac_sha256_digital_signature(self) -> None:
        sig = self.crypto.sign_transaction("TX_100", "ACC_A", "ACC_B", 500.0, "2026-09-28T12:00:00")
        self.assertTrue(len(sig) == 64)

        # Valid signature
        valid = self.crypto.verify_transaction_signature("TX_100", "ACC_A", "ACC_B", 500.0, "2026-09-28T12:00:00", sig)
        self.assertTrue(valid)

        # Tampered amount must fail verification
        tampered = self.crypto.verify_transaction_signature("TX_100", "ACC_A", "ACC_B", 500.01, "2026-09-28T12:00:00", sig)
        self.assertFalse(tampered)

    def test_tamper_proof_audit_ledger(self) -> None:
        h1 = self.ledger.append_audit_entry("TX1", "APPROVE", 0.02, "Clean")
        h2 = self.ledger.append_audit_entry("TX2", "FLAG", 0.45, "ATO Suspicious")
        self.assertEqual(len(self.ledger.chain), 2)

        # Integrity check passes
        is_valid, _ = self.ledger.verify_chain_integrity()
        self.assertTrue(is_valid)

        # Simulate adversarial tamper with past record in database
        self.ledger.chain[0]["decision"] = "TAMPERED_DECISION"
        is_corrupted, bad_idx = self.ledger.verify_chain_integrity()
        self.assertFalse(is_corrupted)
        self.assertEqual(bad_idx, 1)

    def test_rate_limiter_token_bucket(self) -> None:
        client_ip = "192.168.1.100"
        # 3 requests allowed (capacity = 3)
        self.assertTrue(self.limiter.allow_request(client_ip)[0])
        self.assertTrue(self.limiter.allow_request(client_ip)[0])
        self.assertTrue(self.limiter.allow_request(client_ip)[0])

        # 4th request must be blocked
        allowed, _ = self.limiter.allow_request(client_ip)
        self.assertFalse(allowed)

    def test_sanitizer_sql_and_xss_detection(self) -> None:
        sql_attack = "ACC_ALICE' OR 1=1; DROP TABLE core_accounts; --"
        is_threat, threats = SecuritySanitizer.inspect_input(sql_attack)
        self.assertTrue(is_threat)
        self.assertTrue(any("SQL_INJECTION" in t for t in threats))

        xss_attack = "<script>alert('pwned');</script>"
        is_threat_xss, threats_xss = SecuritySanitizer.inspect_input(xss_attack)
        self.assertTrue(is_threat_xss)
        self.assertTrue(any("XSS" in t for t in threats_xss))


class TestMultiLanguageEngines(unittest.TestCase):
    """Tests COBOL mainframe card processing and Fortran Monte Carlo numerical computation."""

    def test_cobol_mainframe_engine(self) -> None:
        # Benign record
        rec_benign = CobolScreeningRecord("TX_COBOL_001", "ACC_ALICE", "ACC_BOB", 50.0, 60.0, False, False)
        card = CobolMainframeEngine.format_80_col_card(rec_benign)
        self.assertEqual(len(card), 80)
        decision, risk, _ = CobolMainframeEngine.execute_mainframe_batch(rec_benign)
        self.assertEqual(decision, "APPROVE")

        # Account takeover record
        rec_ato = CobolScreeningRecord("TX_COBOL_002", "ACC_CHARLIE", "ACC_BOB", 4500.0, 75.0, True, False)
        decision_ato, risk_ato, reason = CobolMainframeEngine.execute_mainframe_batch(rec_ato)
        self.assertEqual(decision_ato, "FLAG_MANUAL_REVIEW")
        self.assertEqual(reason, "RULE-ATO-NEW-DEVICE-BURST")

    def test_fortran_numerical_monte_carlo(self) -> None:
        # Simulate high-risk transaction VaR
        res = FortranRiskEngine.simulate_var_cvar(base_amount=5000.0, p_fraud=0.40, n_simulations=2000, seed=123)
        self.assertEqual(res["confidence_level"], 0.99)
        self.assertGreater(res["value_at_risk_99"], 5000.0)
        self.assertGreater(res["expected_shortfall_cvar"], res["value_at_risk_99"])


if __name__ == "__main__":
    unittest.main()
