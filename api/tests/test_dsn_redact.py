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
