"""Redaction centralizada para logs, erros, auditoria e resultados."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"

_SENSITIVE_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "set_cookie",
    "private_key",
    "client_secret",
    "credential",
    "credentials",
}

_TEXT_PATTERNS = (
    (re.compile(r"-----BEGIN [^-\r\n]+PRIVATE KEY-----.*?-----END [^-\r\n]+PRIVATE KEY-----", re.S), "[REDACTED PRIVATE KEY]"),
    (re.compile(r"(?i)(Bearer\s+)[^\s,;]+"), r"\1" + REDACTED),
    (re.compile(r"(?i)(Cookie:\s*)[^\r\n]+"), r"\1" + REDACTED),
    (re.compile(r"(?i)(Set-Cookie:\s*)[^\r\n]+"), r"\1" + REDACTED),
    (re.compile(r"([a-z][a-z0-9+.-]*://)([^/\s:@]+):([^@\s/]+)@"), r"\1" + REDACTED + "@"),
    (re.compile(r"(?i)([?&](?:api[_-]?key|access[_-]?token|refresh[_-]?token|token|password|secret|key)=)[^&#\s]+"), r"\1" + REDACTED),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"), "[REDACTED TOKEN]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED TOKEN]"),
    (re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|password|secret)\s*([:=])\s*[^\s,;]+"), lambda match: f"{match.group(1)}{match.group(2)}{REDACTED}"),
)


def redact_text(value: str) -> str:
    result = value
    for pattern, replacement in _TEXT_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def redact(value: Any, *, key: str | None = None) -> Any:
    """Copia JSON-like data e substitui campos/padrões sensíveis."""

    if key is not None:
        normalized = key.lower().replace("-", "_")
        if normalized in _SENSITIVE_KEYS or normalized.endswith("_secret"):
            return REDACTED
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        return {str(item_key): redact(item_value, key=str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return [redact(item) for item in value]
    return value
