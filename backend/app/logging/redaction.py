import re
from typing import Any

REDACTED = "***REDACTED***"

SENSITIVE_KEYS = frozenset({
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "session_id",
    "session_secret",
    "credentials",
    "private_key",
    "access_token",
    "refresh_token",
})

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(s in normalized for s in SENSITIVE_KEYS)


def mask_email(value: str) -> str:
    def _mask(match: re.Match) -> str:
        email = match.group()
        local, domain = email.split("@", 1)
        return f"{local[0]}***@***.{domain.rsplit('.', 1)[-1]}"
    return EMAIL_PATTERN.sub(_mask, value)


def mask_phone(value: str) -> str:
    def _mask(match: re.Match) -> str:
        digits = re.sub(r"[^0-9]", "", match.group())
        return f"***-***-{digits[-4:]}"
    return PHONE_PATTERN.sub(_mask, value)


def redact_value(value: str) -> str:
    value = mask_email(value)
    value = mask_phone(value)
    return value


def redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    cleaned = {}
    for key, value in data.items():
        if _is_sensitive_key(key):
            cleaned[key] = REDACTED
        elif isinstance(value, str):
            cleaned[key] = redact_value(value)
        elif isinstance(value, dict):
            cleaned[key] = redact_dict(value)
        elif isinstance(value, list):
            cleaned[key] = [
                redact_dict(item) if isinstance(item, dict)
                else redact_value(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            cleaned[key] = value
    return cleaned
