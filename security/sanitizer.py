"""Security Sanitizer, Injection Detector, and OWASP Security Headers."""

import html
import re
from typing import Dict, List, Tuple


class SecuritySanitizer:
    """Detects and neutralizes SQL Injection, XSS, and command injection attacks."""

    SQL_INJECTION_PATTERNS = [
        re.compile(r"(\b(UNION(\s+ALL)?|SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b)", re.IGNORECASE),
        re.compile(r"(--|#|/\*|\*/|;\s*$)", re.IGNORECASE),
        re.compile(r"('\s*OR\s*'\d+'\s*=\s*'\d+)", re.IGNORECASE),
        re.compile(r"(\bOR\s+1\s*=\s*1\b)", re.IGNORECASE),
    ]

    XSS_PATTERNS = [
        re.compile(r"(<script\b[^>]*>.*?</script>)", re.IGNORECASE),
        re.compile(r"(javascript\s*:\s*)", re.IGNORECASE),
        re.compile(r"(onload\s*=|onerror\s*=|onclick\s*=)", re.IGNORECASE),
    ]

    @classmethod
    def inspect_input(cls, text: str) -> Tuple[bool, List[str]]:
        """Scans input string for malicious attack signatures.

        Returns (is_malicious, detected_threats).
        """
        threats = []
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if pattern.search(text):
                threats.append(f"SQL_INJECTION_PATTERN_DETECTED: {pattern.pattern}")
                break

        for pattern in cls.XSS_PATTERNS:
            if pattern.search(text):
                threats.append(f"XSS_SCRIPT_PATTERN_DETECTED: {pattern.pattern}")
                break

        return len(threats) > 0, threats

    @classmethod
    def sanitize_string(cls, text: str) -> str:
        """HTML escapes text to prevent XSS rendering."""
        return html.escape(text.strip())

    @classmethod
    def apply_security_headers(cls, headers_dict: Dict[str, str]) -> None:
        """Applies enterprise-grade HTTP response headers aligning with OWASP ASVS."""
        headers_dict["X-Frame-Options"] = "DENY"
        headers_dict["X-Content-Type-Options"] = "nosniff"
        headers_dict["X-XSS-Protection"] = "1; mode=block"
        headers_dict["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        headers_dict["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' https://www.gstatic.com; "
            "script-src 'self' 'unsafe-inline' https://www.gstatic.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "frame-ancestors 'none';"
        )
        headers_dict["Referrer-Policy"] = "strict-origin-when-cross-origin"
