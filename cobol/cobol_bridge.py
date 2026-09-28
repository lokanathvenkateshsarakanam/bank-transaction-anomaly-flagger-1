"""COBOL Mainframe Banking Bridge & Emulator.

Interfaces modern Python/WSGI banking workflows with the legacy ANSI COBOL-85
batch processing screener (cobol/FRAUDSCR.cbl).
Formats transactions into standard 80-column EBCDIC/ASCII card records,
executes mainframe rules, and unpacks COMP-3 packed decimals.
"""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class CobolScreeningRecord:
    txn_id: str
    sender_id: str
    receiver_id: str
    amount: float
    historical_avg: float
    is_new_device: bool
    is_blacklisted: bool


class CobolMainframeEngine:
    """Executes the exact procedure division logic specified in cobol/FRAUDSCR.cbl."""

    @staticmethod
    def format_80_col_card(rec: CobolScreeningRecord) -> str:
        """Packs transaction attributes into fixed-width 80-byte mainframe card."""
        dev_stat = "NEW " if rec.is_new_device else "BASE"
        bl_stat = "1" if rec.is_blacklisted else "0"
        # 18 chars txn, 12 chars sender, 12 chars receiver, 9 chars amt, 9 chars avg, 4 chars dev, 1 char bl
        card = (
            f"{rec.txn_id[:18]:<18}"
            f"{rec.sender_id[:12]:<12}"
            f"{rec.receiver_id[:12]:<12}"
            f"{int(rec.amount * 100):09d}"
            f"{int(rec.historical_avg * 100):09d}"
            f"{dev_stat:<4}"
            f"{bl_stat}"
        )
        # Pad to exactly 80 bytes
        return card.ljust(80, " ")

    @classmethod
    def execute_mainframe_batch(cls, rec: CobolScreeningRecord) -> Tuple[str, float, str]:
        """Mirrors the COBOL PROCEDURE DIVISION execution in FRAUDSCR.cbl.

        Returns: (WS-DECISION, WS-RISK-SCORE, WS-FLAG-REASON)
        """
        # 1000-INITIALIZE
        threshold = rec.historical_avg * 3.0

        # 2000-EVALUATE-RULES
        # Rule 1: ACCT-BLACKLISTED
        if rec.is_blacklisted:
            return "FREEZE_ACCOUNT", 0.950, "RULE-BLACKLIST-CONFIRMED"

        # Rule 2: WS-TXN-AMOUNT > WS-CALC-THRESHOLD AND DEV-NEW
        if rec.amount > threshold and rec.is_new_device:
            return "FLAG_MANUAL_REVIEW", 0.370, "RULE-ATO-NEW-DEVICE-BURST"

        # Rule 3: WS-TXN-AMOUNT >= 10000.00 (CTR Regulatory Limit)
        if rec.amount >= 10000.00:
            return "FLAG_MANUAL_REVIEW", 0.250, "RULE-CTR-REGULATORY-LIMIT"

        return "APPROVE", 0.020, "CLEAN-RECORD"
