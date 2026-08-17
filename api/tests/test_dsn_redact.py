import logging

from api.sanitize import (
    RedactSecretsFilter,
    dsn_safe_summary as api_dsn_safe_summary,
    redact_secrets as api_redact_secrets,
    redacted_exception as api_redacted_exception,
)
from etl.sanitize import dsn_safe_summary, redact_secrets, redacted_exception


def test_redact_secrets_strips_userinfo():
    raw = "failed postgresql://alice:s3cret@db.example.com:5432/app?sslmode=require boom"
    out = redact_secrets(raw)
    assert "s3cret" not in out
    assert "alice:***@" in out
    assert "postgresql://" in out


def test_dsn_safe_summary_omits_host_and_password():
    summary = dsn_safe_summary(
        "postgresql://alice:s3cret@shinkansen.example.net:47256/railway?sslmode=require"
    )
    assert "s3cret" not in summary
    assert "alice" not in summary
    assert "shinkansen" not in summary
    assert "host_configured=True" in summary
    assert "sslmode=require" in summary


def test_redacted_exception_masks_url():
    exc = RuntimeError("postgresql://bob:hunter2@localhost/db")
    text = redacted_exception(exc)
    assert "hunter2" not in text
    assert "bob:***@" in text


def test_api_sanitize_matches_etl():
    raw = "failed postgresql://alice:s3cret@db.example.com:5432/app?sslmode=require boom"
    assert api_redact_secrets(raw) == redact_secrets(raw)
    assert api_dsn_safe_summary(raw) == dsn_safe_summary(raw)
    exc = RuntimeError(raw)
    assert api_redacted_exception(exc) == redacted_exception(exc)


def test_log_filter_redacts_dsn(caplog):
    logger = logging.getLogger("sv_redact_test")
    logger.setLevel(logging.ERROR)
    logger.addFilter(RedactSecretsFilter())
    with caplog.at_level(logging.ERROR, logger="sv_redact_test"):
        logger.error("fail postgresql://bob:hunter2@localhost/db")
    assert "hunter2" not in caplog.text
    assert "bob:***@" in caplog.text
