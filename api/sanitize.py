"""Redact database credentials from logs and exception messages."""

from __future__ import annotations

import logging
import re
from urllib.parse import parse_qs, urlparse

# postgres://, postgresql://, postgresql+psycopg://
_URL_RE = re.compile(
    r"(?:postgres(?:ql)?(?:\+[A-Za-z0-9_]+)?)://[^\s'\"<>]+",
    re.IGNORECASE,
)
_USERINFO_RE = re.compile(r"(?<=://)([^:/?#\s]+):([^@/\s]+)@")


def redact_secrets(text: str | None) -> str:
    """Strip userinfo from postgres URLs and any user:pass@ fragments."""
    if not text:
        return "" if text is None else text

    def _mask_url(match: re.Match[str]) -> str:
        return _USERINFO_RE.sub(r"\1:***@", match.group(0))

    redacted = _URL_RE.sub(_mask_url, text)
    return _USERINFO_RE.sub(r"\1:***@", redacted)


def dsn_safe_summary(dsn: str | None) -> str:
    """Non-secret connection metadata (no host, user, or password)."""
    if not dsn:
        return "dsn=missing"
    try:
        parsed = urlparse(dsn)
        sslmode = ""
        if parsed.query:
            sslmode = parse_qs(parsed.query).get("sslmode", [""])[0]
        scheme = parsed.scheme or "unknown"
        return (
            f"scheme={scheme} host_configured={bool(parsed.hostname)} "
            f"sslmode={sslmode or 'unset'}"
        )
    except Exception:
        return "dsn=unparseable"


def redacted_exception(exc: BaseException) -> str:
    return redact_secrets(f"{type(exc).__name__}: {exc}")


class RedactSecretsFilter(logging.Filter):
    """Drop credentials from log records (uvicorn traces include driver errors)."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = redact_secrets(record.getMessage())
        except Exception:
            message = redact_secrets(str(record.msg))
        record.msg = message
        record.args = ()
        if record.exc_text:
            record.exc_text = redact_secrets(record.exc_text)
        return True


def install_log_redaction() -> None:
    filt = RedactSecretsFilter()
    logging.getLogger().addFilter(filt)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(name).addFilter(filt)
