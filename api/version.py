import os

API_VERSION = "0.1.0"

_SHA_ENV_KEYS = ("RAILWAY_GIT_COMMIT_SHA", "GIT_SHA", "SOURCE_COMMIT")


def git_sha() -> str:
    for key in _SHA_ENV_KEYS:
        raw = os.getenv(key)
        if raw and raw.strip():
            return raw.strip()[:7]
    return "dev"


def deployment_id() -> str | None:
    raw = os.getenv("RAILWAY_DEPLOYMENT_ID")
    if raw and raw.strip():
        return raw.strip()
    return None


def public_build() -> dict[str, str | None]:
    return {
        "version": API_VERSION,
        "git_sha": git_sha(),
        "deployment_id": deployment_id(),
    }
