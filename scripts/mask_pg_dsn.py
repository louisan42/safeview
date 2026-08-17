#!/usr/bin/env python3
"""Emit GitHub Actions ::add-mask:: lines for Postgres DSN env vars.

Never prints a DSN except as a mask directive (required for GHA log redaction).
"""

from __future__ import annotations

import argparse
import os
import sys
from urllib.parse import parse_qs, unquote, urlencode, urlparse, urlunparse

GENERIC = {
    "postgres",
    "postgresql",
    "railway",
    "require",
    "public",
    "sslmode",
}

KNOWN_DSN_VARS = (
    "PG_DSN",
    "DATABASE_URL",
    "PROD_PG_DSN",
    "SOURCE_PG_DSN",
    "STAGING_PG_DSN",
)


def mask(value: str) -> None:
    value = (value or "").strip()
    if len(value) < 4 or value.lower() in GENERIC:
        return
    print(f"::add-mask::{value}")


def mask_dsn(dsn: str) -> None:
    mask(dsn)
    parsed = urlparse(dsn)
    if parsed.password:
        mask(parsed.password)
        mask(unquote(parsed.password))
    if parsed.hostname:
        mask(parsed.hostname)
    if parsed.username and ("." in parsed.username or len(parsed.username) > 12):
        mask(parsed.username)
        mask(unquote(parsed.username))
    if parsed.scheme and parsed.netloc:
        query = parse_qs(parsed.query)
        for sslmode in (None, "require"):
            q = dict(query)
            if sslmode:
                q["sslmode"] = [sslmode]
            reconstructed = urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    urlencode(q, doseq=True),
                    parsed.fragment,
                )
            )
            mask(reconstructed)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mask Postgres DSN env vars in GitHub Actions")
    parser.add_argument(
        "--require",
        action="append",
        default=[],
        help="Env var that must be set (repeatable)",
    )
    parser.add_argument(
        "--require-any",
        action="append",
        default=[],
        help="Comma-separated env var names; at least one must be set (repeatable)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    for name in args.require:
        if not (os.environ.get(name) or "").strip():
            print(f"{name} secret is missing.", file=sys.stderr)
            return 1
    for group in args.require_any:
        names = [n.strip() for n in group.split(",") if n.strip()]
        if names and not any((os.environ.get(n) or "").strip() for n in names):
            print("Missing source DSN secret (PROD_PG_DSN or SOURCE_PG_DSN).", file=sys.stderr)
            return 1

    seen: set[str] = set()
    for name in (*KNOWN_DSN_VARS, *args.require):
        raw = (os.environ.get(name) or "").strip()
        if not raw or raw in seen:
            continue
        seen.add(raw)
        mask_dsn(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
