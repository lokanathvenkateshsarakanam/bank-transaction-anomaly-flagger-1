"""Transaction domain model (OOPJ).

Encapsulates individual transaction data payload transferred across the banking network.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from models.types import ChannelType, TransactionStatus


@dataclass
class Transaction:
    """Represents a financial transaction moving funds between two accounts."""

    txn_id: str
    sender_id: str
    receiver_id: str
    amount: float
    timestamp: datetime = field(default_factory=datetime.now)
    channel: ChannelType = ChannelType.ONLINE_BANKING
    location: str = "US"
    device_id: str = "device_default"
    ip_address: str = "127.0.0.1"
    status: TransactionStatus = TransactionStatus.PENDING
    flag_reasons: List[str] = field(default_factory=list)
    risk_score: float = 0.0

    def add_flag(self, reason: str) -> None:
        """Appends a detected risk rule or anomaly flag reason."""
        if reason not in self.flag_reasons:
            self.flag_reasons.append(reason)

    def mark_approved(self) -> None:
        self.status = TransactionStatus.APPROVED

    def mark_flagged(self) -> None:
        self.status = TransactionStatus.FLAGGED_FOR_REVIEW

    def mark_blocked(self) -> None:
        self.status = TransactionStatus.BLOCKED

    def __repr__(self) -> str:
        return (
            f"Transaction({self.txn_id}: {self.sender_id} -> {self.receiver_id}, "
            f"${self.amount:.2f}, status={self.status.value}, risk={self.risk_score:.2f})"
        )
