"""Role-Based Access Control (RBAC) and API Authentication."""

from enum import Enum
import hmac
import secrets
from typing import Dict, Optional, Set


class UserRole(Enum):
    ANALYST = "ANALYST"
    ADMIN = "ADMIN"
    SYSTEM_SERVICE = "SYSTEM_SERVICE"


class SecurityAuthManager:
    """Manages API Keys, Bearer tokens, and role-based permissions."""

    def __init__(self) -> None:
        self._api_keys: Dict[str, UserRole] = {
            "bank_analyst_key_secure_2026": UserRole.ANALYST,
            "bank_admin_master_key_9988": UserRole.ADMIN,
            "bank_system_internal_service": UserRole.SYSTEM_SERVICE,
        }

    def register_key(self, key: str, role: UserRole) -> None:
        self._api_keys[key] = role

    def generate_secure_key(self, role: UserRole) -> str:
        new_key = f"key_{secrets.token_hex(24)}"
        self._api_keys[new_key] = role
        return new_key

    def authenticate(self, provided_key: Optional[str]) -> Optional[UserRole]:
        """Constant-time token validation to prevent timing attacks."""
        if not provided_key:
            return None
        for stored_key, role in self._api_keys.items():
            if hmac.compare_digest(stored_key, provided_key):
                return role
        return None

    def authorize(self, role: Optional[UserRole], required_roles: Set[UserRole]) -> bool:
        if not role:
            return False
        if role == UserRole.ADMIN:
            return True  # Admin inherits all permissions
        return role in required_roles


auth_manager = SecurityAuthManager()
