"""Account domain model embodying OOP principles (Encapsulation, Data Integrity).

Represents bank accounts with identity metadata used by DMGT relations and
behavioral baselines used by Propositional Logic and AI agent rules.
"""

from datetime import datetime
from typing import Optional
from models.types import KYCStatus


class Account:
    """Represents a bank account entity with behavioral baselines and identity markers."""

    def __init__(
        self,
        account_id: str,
        holder_name: str,
        initial_balance: float = 0.0,
        kyc_status: KYCStatus = KYCStatus.TIER_2_VERIFIED,
        created_at: Optional[datetime] = None,
        device_fingerprint: str = "",
        ip_address: str = "",
        national_id: str = "",
        historical_avg_amount: float = 100.0,
        historical_std_amount: float = 25.0,
        is_blacklisted: bool = False,
    ) -> None:
        self._account_id = account_id
        self._holder_name = holder_name
        self._balance = max(0.0, float(initial_balance))
        self._kyc_status = kyc_status
        self._created_at = created_at or datetime.now()
        self._device_fingerprint = device_fingerprint
        self._ip_address = ip_address
        self._national_id = national_id
        self._historical_avg_amount = max(1.0, float(historical_avg_amount))
        self._historical_std_amount = max(0.5, float(historical_std_amount))
        self._transaction_count: int = 0
        self._is_blacklisted = is_blacklisted

    # Getters (Encapsulation)
    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def holder_name(self) -> str:
        return self._holder_name

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def kyc_status(self) -> KYCStatus:
        return self._kyc_status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def device_fingerprint(self) -> str:
        return self._device_fingerprint

    @property
    def ip_address(self) -> str:
        return self._ip_address

    @property
    def national_id(self) -> str:
        return self._national_id

    @property
    def historical_avg_amount(self) -> float:
        return self._historical_avg_amount

    @property
    def historical_std_amount(self) -> float:
        return self._historical_std_amount

    @property
    def transaction_count(self) -> int:
        return self._transaction_count

    @property
    def is_blacklisted(self) -> bool:
        return self._is_blacklisted

    @is_blacklisted.setter
    def is_blacklisted(self, value: bool) -> None:
        self._is_blacklisted = bool(value)

    def deposit(self, amount: float) -> None:
        """Credits funds to account."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self._balance += amount

    def withdraw(self, amount: float) -> bool:
        """Debits funds from account if sufficient balance."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if self._balance < amount:
            return False
        self._balance -= amount
        return True

    def record_transaction(self, amount: float) -> None:
        """Incrementally updates running transaction statistics."""
        self._transaction_count += 1
        # Welford-like moving average approximation for demonstration
        alpha = 0.1
        self._historical_avg_amount = (1 - alpha) * self._historical_avg_amount + alpha * amount

    def account_age_days(self, current_time: Optional[datetime] = None) -> float:
        """Returns account age in days."""
        now = current_time or datetime.now()
        delta = now - self._created_at
        return max(0.0, delta.total_seconds() / 86400.0)

    def __repr__(self) -> str:
        return f"Account(id='{self._account_id}', holder='{self._holder_name}', balance=${self._balance:.2f})"
