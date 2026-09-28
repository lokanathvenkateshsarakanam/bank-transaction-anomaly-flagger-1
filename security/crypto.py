"""Enterprise Banking Cryptography Suite.

Implements:
1. AES-256-GCM Authenticated Encryption for sensitive financial PII (SSN, national ID).
2. HMAC-SHA256 Digital Signature verification for transaction integrity.
3. Cryptographic Tamper-Proof Audit Chaining (Merkle-style ledger integrity).
"""

import base64
import hashlib
import hmac
import os
import secrets
from typing import Dict, List, Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EnterpriseCryptoManager:
    """Manages encryption, digital signatures, and audit block hashing."""

    def __init__(self, master_key: Optional[bytes] = None) -> None:
        # 256-bit AES master key
        self.master_key = master_key or secrets.token_bytes(32)
        self.hmac_secret = secrets.token_bytes(32)
        self._aesgcm = AESGCM(self.master_key)

    def encrypt_pii(self, plaintext: str) -> str:
        """Encrypts sensitive field using AES-256-GCM with a random 96-bit nonce.

        Returns base64 encoded string: nonce + ciphertext + tag.
        """
        if not plaintext:
            return ""
        nonce = secrets.token_bytes(12)
        encrypted_bytes = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        combined = nonce + encrypted_bytes
        return base64.b64encode(combined).decode("utf-8")

    def decrypt_pii(self, encrypted_b64: str) -> str:
        """Decrypts AES-256-GCM ciphertext."""
        if not encrypted_b64:
            return ""
        combined = base64.b64decode(encrypted_b64.encode("utf-8"))
        nonce = combined[:12]
        ciphertext_with_tag = combined[12:]
        decrypted_bytes = self._aesgcm.decrypt(nonce, ciphertext_with_tag, None)
        return decrypted_bytes.decode("utf-8")

    def sign_transaction(
        self,
        txn_id: str,
        sender_id: str,
        receiver_id: str,
        amount: float,
        timestamp_str: str,
    ) -> str:
        """Generates HMAC-SHA256 digital signature over canonical transaction payload."""
        canonical_msg = f"{txn_id}|{sender_id}|{receiver_id}|{amount:.2f}|{timestamp_str}"
        sig = hmac.new(self.hmac_secret, canonical_msg.encode("utf-8"), hashlib.sha256).hexdigest()
        return sig

    def verify_transaction_signature(
        self,
        txn_id: str,
        sender_id: str,
        receiver_id: str,
        amount: float,
        timestamp_str: str,
        signature: str,
    ) -> bool:
        """Constant-time verification of HMAC signature to prevent timing attacks."""
        expected_sig = self.sign_transaction(txn_id, sender_id, receiver_id, amount, timestamp_str)
        return hmac.compare_digest(expected_sig, signature)


class TamperProofAuditLedger:
    """Cryptographic hash-chained audit ledger ensuring historical records cannot be altered."""

    def __init__(self) -> None:
        self.chain: List[Dict[str, any]] = []
        self.genesis_hash = hashlib.sha256(b"GENESIS_BANK_AUDIT_BLOCK_00000000").hexdigest()

    @property
    def latest_hash(self) -> str:
        if not self.chain:
            return self.genesis_hash
        return self.chain[-1]["block_hash"]

    def append_audit_entry(self, txn_id: str, decision: str, risk_score: float, audit_trace: str) -> str:
        """Appends a new record chained to the previous block hash."""
        prev_hash = self.latest_hash
        payload = f"{prev_hash}|{txn_id}|{decision}|{risk_score:.4f}|{audit_trace}"
        curr_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        entry = {
            "index": len(self.chain) + 1,
            "prev_hash": prev_hash,
            "block_hash": curr_hash,
            "txn_id": txn_id,
            "decision": decision,
            "risk_score": risk_score,
            "audit_trace": audit_trace,
        }
        self.chain.append(entry)
        return curr_hash

    def verify_chain_integrity(self) -> Tuple[bool, Optional[int]]:
        """Verifies the entire cryptographic ledger chain.

        Returns (is_valid, corrupted_block_index).
        """
        for i, block in enumerate(self.chain):
            prev = self.genesis_hash if i == 0 else self.chain[i - 1]["block_hash"]
            if block["prev_hash"] != prev:
                return False, i + 1
            payload = f"{prev}|{block['txn_id']}|{block['decision']}|{block['risk_score']:.4f}|{block['audit_trace']}"
            recomputed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            if recomputed != block["block_hash"]:
                return False, i + 1
        return True, None


# Global security instances
crypto_manager = EnterpriseCryptoManager()
audit_ledger = TamperProofAuditLedger()
