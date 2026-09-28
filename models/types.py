"""Type definitions and enums for the Bank Transaction Anomaly Flagger.

Maps to OOPJ domain model & AI action spaces.
"""

from enum import Enum, auto


class TransactionStatus(Enum):
    """Lifecycle status of a financial transaction."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    FLAGGED_FOR_REVIEW = "FLAGGED_FOR_REVIEW"
    BLOCKED = "BLOCKED"


class ActionType(Enum):
    """Rational Agent action space (PEAS: Actuators)."""
    APPROVE = "APPROVE"
    FLAG_MANUAL_REVIEW = "FLAG_MANUAL_REVIEW"
    FREEZE_ACCOUNT = "FREEZE_ACCOUNT"


class RiskTier(Enum):
    """Categorical risk assessment tiers."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class KYCStatus(Enum):
    """Account holder verification levels."""
    TIER_1_UNVERIFIED = "TIER_1_UNVERIFIED"
    TIER_2_VERIFIED = "TIER_2_VERIFIED"
    TIER_3_PREMIUM = "TIER_3_PREMIUM"


class ChannelType(Enum):
    """Payment channels."""
    ONLINE_BANKING = "ONLINE_BANKING"
    MOBILE_APP = "MOBILE_APP"
    ATM = "ATM"
    WIRE_TRANSFER = "WIRE_TRANSFER"
    POS = "POS"
