#!/usr/bin/env python3
"""Fail CI if workflows or scripts would echo a Postgres URL / DSN env var."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCAN_GLOBS = (
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    "scripts/*.py",
    "scripts/*.sh",
    "etl/*.py",
    "api/*.py",
    "api/routers/*.py",
)

# echo/printf of a DSN env expansion, but not ::add-mask:: or quoted name-only messages.
ECHO_DSN_RE = re.compile(
    r"(?i)(?<!::add-mask::)(?:echo|printf)\s+.*(?:\$\{?(?:PROD_PG_DSN|SOURCE_PG_DSN|STAGING_PG_DSN|PG_DSN|DATABASE_URL)"
    r"|postgres(?:ql)?(?:\+[A-Za-z0-9_]+)?://[^\s'\"\\]+)",
)

PRINT_DSN_RE = re.compile(
    r"(?i)print\(\s*(?:os\.environ(?:\.get)?\(\s*['\"](?:PROD_PG_DSN|SOURCE_PG_DSN|STAGING_PG_DSN|PG_DSN|DATABASE_URL)"
    r"|f?['\"][^'\"]*postgres(?:ql)?://[^\s'\"]+:[^@\s'\"]+@)",
)

# Bare echo of postgres:// in a run: block (not a comment).
LITERAL_URL_ECHO_RE = re.compile(
    r"(?i)^\s*(?:-\s*)?(?:run:\s*)?(?:echo|printf)\s+['\"][^'\"]*postgres(?:ql)?://",
    re.MULTILINE,
)


def _iter_files() -> list[Path]:
    files: list[Path] = []
    for pattern in SCAN_GLOBS:
        files.extend(ROOT.glob(pattern))
    return sorted({path for path in files if path.is_file()})


def scan_text(text: str) -> list[str]:
    hits: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        if "::add-mask::" in line:
            continue
        if "dsn_safe_summary" in line or "redact_secrets" in line:
            continue
        if ECHO_DSN_RE.search(line) or PRINT_DSN_RE.search(line) or LITERAL_URL_ECHO_RE.search(line):
            hits.append(f"{lineno}:{stripped}")
    return hits


def main() -> int:
    failed = False
    for path in _iter_files():
        rel = path.relative_to(ROOT)
        hits = scan_text(path.read_text(encoding="utf-8"))
        if hits:
            failed = True
            print(f"{rel}: would echo a Postgres URL / DSN", file=sys.stderr)
            for hit in hits:
                print(f"  {hit}", file=sys.stderr)
    if failed:
        return 1
    print("secret hygiene ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
