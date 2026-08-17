#!/usr/bin/env python3
"""Copy selected PostGIS objects from production to staging. Never logs DSNs."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from etl.sanitize import dsn_safe_summary, redact_secrets

DUMP_TABLES = (
    "tps_incidents",
    "cot_neighbourhoods_158",
    "etl_metadata",
    "v_incidents_daily",
    "v_incidents_by_neighbourhood",
    "v_incidents_last_30d",
)

COUNT_SQL = """
SELECT
  (SELECT COUNT(*) FROM tps_incidents) AS incidents,
  (SELECT COUNT(*) FROM cot_neighbourhoods_158) AS neighbourhoods,
  (SELECT COUNT(*) FROM etl_metadata) AS metadata;
"""

_CONNINFO_RE = re.compile(
    r'connection to server at "[^"]+"(?:\s+\([^)]+\))?, port \d+',
    re.IGNORECASE,
)


def _redact_cmd_output(text: str) -> str:
    return _CONNINFO_RE.sub(
        'connection to server at "[redacted]", port [redacted]',
        redact_secrets(text),
    )


def _source_dsn() -> str:
    return (os.environ.get("PROD_PG_DSN") or os.environ.get("SOURCE_PG_DSN") or "").strip()


def _dest_dsn() -> str:
    return (os.environ.get("STAGING_PG_DSN") or "").strip()


def ensure_sslmode(dsn: str, default: str = "require") -> str:
    parsed = urlparse(dsn)
    if not parsed.scheme or not parsed.hostname:
        return dsn
    query = parse_qs(parsed.query)
    if query.get("sslmode"):
        return dsn
    query["sslmode"] = [default]
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query, doseq=True),
            parsed.fragment,
        )
    )


def with_sslmode(dsn: str, mode: str) -> str:
    parsed = urlparse(dsn)
    query = parse_qs(parsed.query)
    query["sslmode"] = [mode]
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query, doseq=True),
            parsed.fragment,
        )
    )


def _hosts_match(source: str, dest: str) -> bool:
    src = urlparse(source)
    dst = urlparse(dest)
    if not src.hostname or not dst.hostname:
        return False
    src_key = (src.hostname.lower(), src.port, (src.path or "").rstrip("/").lower())
    dst_key = (dst.hostname.lower(), dst.port, (dst.path or "").rstrip("/").lower())
    return src_key == dst_key


def _run(cmd: list[str], *, label: str) -> None:
    try:
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        print(f"[staging-db] missing command for {label}: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    if completed.returncode != 0:
        combined = f"{completed.stdout or ''}\n{completed.stderr or ''}"
        print(f"[staging-db] {label} failed", file=sys.stderr)
        print(_redact_cmd_output(combined), file=sys.stderr)
        raise SystemExit(completed.returncode or 1)


def _print_version(tool: str) -> None:
    completed = subprocess.run([tool, "--version"], check=False, capture_output=True, text=True)
    text = (completed.stdout or completed.stderr or "").strip()
    print(f"[staging-db] {text or tool + ' version unknown'}")


def _psql_scalar(dsn: str, sql: str) -> str:
    completed = subprocess.run(
        ["psql", "--dbname", dsn, "-v", "ON_ERROR_STOP=1", "-tAc", sql],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        print("[staging-db] count query failed", file=sys.stderr)
        print(_redact_cmd_output(completed.stderr or ""), file=sys.stderr)
        raise SystemExit(completed.returncode or 1)
    return (completed.stdout or "").strip()


def _probe_dsn(dsn: str) -> bool:
    completed = subprocess.run(
        ["psql", "--dbname", dsn, "-v", "ON_ERROR_STOP=1", "-tAc", "SELECT 1"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0 and (completed.stdout or "").strip() == "1"


def _dest_with_working_ssl(dest: str) -> str:
    for mode in ("require", "prefer", "disable"):
        candidate = with_sslmode(dest, mode)
        if _probe_dsn(candidate):
            print(f"[staging-db] dest sslmode={mode}")
            return candidate
    print("[staging-db] could not connect to staging Postgres", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    source = ensure_sslmode(_source_dsn(), default="require")
    dest = ensure_sslmode(_dest_dsn(), default="prefer")
    if not source or not dest:
        print(
            "[staging-db] Missing DSN. Set PROD_PG_DSN (or SOURCE_PG_DSN) and STAGING_PG_DSN.",
            file=sys.stderr,
        )
        return 1
    if _hosts_match(source, dest):
        print("[staging-db] Refusing restore: source and destination hosts match.", file=sys.stderr)
        return 1

    print(f"[staging-db] source {dsn_safe_summary(source)}")
    dest = _dest_with_working_ssl(dest)
    print(f"[staging-db] dest {dsn_safe_summary(dest)}")
    for tool in ("pg_dump", "pg_restore", "psql"):
        _print_version(tool)

    dump_fd, dump_name = tempfile.mkstemp(prefix="sv-pg-", suffix=".dump")
    os.close(dump_fd)
    dump_path = Path(dump_name)
    try:
        dump_cmd = [
            "pg_dump",
            "--dbname",
            source,
            "--format=custom",
            "--no-owner",
            "--no-acl",
            "--compress=6",
        ]
        for table in DUMP_TABLES:
            dump_cmd.extend(["--table", table])
        dump_cmd.extend(["--file", str(dump_path)])
        _run(dump_cmd, label="pg_dump")
        size = dump_path.stat().st_size
        print(f"[staging-db] dump wrote {size} bytes")
        if size < 1024:
            print("[staging-db] dump is suspiciously small; aborting", file=sys.stderr)
            return 1

        _run(
            [
                "psql",
                "--dbname",
                dest,
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                "CREATE EXTENSION IF NOT EXISTS postgis;",
            ],
            label="create postgis",
        )
        _run(
            [
                "pg_restore",
                "--dbname",
                dest,
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-acl",
                "--exit-on-error",
                str(dump_path),
            ],
            label="pg_restore",
        )
        counts = _psql_scalar(dest, COUNT_SQL)
        # psql -tAc with three columns: incidents|neighbourhoods|metadata
        parts = counts.split("|")
        if len(parts) == 3:
            print(
                f"[staging-db] restored incidents={parts[0]} "
                f"neighbourhoods={parts[1]} metadata={parts[2]}"
            )
        else:
            print(f"[staging-db] restored counts={counts}")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as handle:
                handle.write("\n## Staging DB refresh\n\n")
                if len(parts) == 3:
                    handle.write(f"- incidents: {parts[0]}\n")
                    handle.write(f"- neighbourhoods: {parts[1]}\n")
                    handle.write(f"- etl_metadata: {parts[2]}\n")
                else:
                    handle.write(f"- counts: {counts}\n")
    finally:
        dump_path.unlink(missing_ok=True)
        print("[staging-db] temp dump deleted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
