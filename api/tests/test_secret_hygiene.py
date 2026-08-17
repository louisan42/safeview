import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hygiene_scan_flags_echo_dsn():
    hygiene = _load("check_secret_hygiene")
    hits = hygiene.scan_text('echo "$PG_DSN"\n')
    assert hits
    hits = hygiene.scan_text('echo "postgresql://alice:s3cret@db.example.com/app"\n')
    assert hits


def test_hygiene_scan_allows_mask_and_safe_summary():
    hygiene = _load("check_secret_hygiene")
    assert not hygiene.scan_text('print(f"::add-mask::{value}")\n')
    assert not hygiene.scan_text('echo "PG_DSN secret is missing."\n')
    assert not hygiene.scan_text('print(dsn_safe_summary(pg_dsn))\n')


def test_hygiene_repo_is_clean():
    hygiene = _load("check_secret_hygiene")
    assert hygiene.main() == 0


def test_mask_pg_dsn_requires_secret(monkeypatch, capsys):
    mask = _load("mask_pg_dsn")
    monkeypatch.delenv("PG_DSN", raising=False)
    assert mask.main(["--require", "PG_DSN"]) == 1
    err = capsys.readouterr().err
    assert "PG_DSN" in err


def test_mask_pg_dsn_emits_add_mask(monkeypatch, capsys):
    mask = _load("mask_pg_dsn")
    dsn = "postgresql://alice:s3cret@db.example.com:5432/app?sslmode=require"
    monkeypatch.setenv("PG_DSN", dsn)
    assert mask.main(["--require", "PG_DSN"]) == 0
    out = capsys.readouterr().out
    assert "::add-mask::s3cret" in out
    assert "::add-mask::db.example.com" in out
    assert dsn in out


def test_refresh_refuses_same_host():
    refresh = _load("refresh_staging_db")
    src = "postgresql://u:p@db.example.com:5432/app"
    dst = "postgresql://u:p@db.example.com:5432/app"
    assert refresh._hosts_match(src, dst)
    assert not refresh._hosts_match(src, "postgresql://u:p@other.example.com:5432/app")


def test_refresh_adds_sslmode():
    refresh = _load("refresh_staging_db")
    dsn = "postgresql://u:p@db.example.com:5432/app"
    out = refresh.ensure_sslmode(dsn)
    assert "sslmode=require" in out
    assert refresh.ensure_sslmode(out) == out
    prefer = refresh.ensure_sslmode(dsn, default="prefer")
    assert "sslmode=prefer" in prefer
    forced = refresh.with_sslmode(dsn, "disable")
    assert "sslmode=disable" in forced


def test_refresh_redacts_psql_conninfo():
    refresh = _load("refresh_staging_db")
    raw = 'psql: error: connection to server at "example.invalid" (1.2.3.4), port 1234 failed'
    out = refresh._redact_cmd_output(raw)
    assert "example.invalid" not in out
    assert "1.2.3.4" not in out
    assert "[redacted]" in out
