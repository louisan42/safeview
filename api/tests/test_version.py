from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from api.main import app
from api.version import API_VERSION, deployment_id, git_sha, public_build


def _clear_sha_env(monkeypatch):
    for key in ("RAILWAY_GIT_COMMIT_SHA", "GIT_SHA", "SOURCE_COMMIT", "RAILWAY_DEPLOYMENT_ID"):
        monkeypatch.delenv(key, raising=False)


class TestGitShaResolution:
    def test_defaults_to_dev_when_no_commit_env(self, monkeypatch):
        _clear_sha_env(monkeypatch)
        assert git_sha() == "dev"

    def test_uses_first_seven_of_railway_git_commit_sha(self, monkeypatch):
        _clear_sha_env(monkeypatch)
        monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "abcdef1234567890")
        assert git_sha() == "abcdef1"

    def test_falls_back_to_git_sha_then_source_commit(self, monkeypatch):
        _clear_sha_env(monkeypatch)
        monkeypatch.setenv("GIT_SHA", "1234567890abcdef")
        assert git_sha() == "1234567"
        monkeypatch.delenv("GIT_SHA")
        monkeypatch.setenv("SOURCE_COMMIT", "deadbeefcafebabe")
        assert git_sha() == "deadbee"

    def test_strips_whitespace_and_ignores_blank(self, monkeypatch):
        _clear_sha_env(monkeypatch)
        monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "  cafe123xyz  ")
        monkeypatch.setenv("GIT_SHA", "ignored")
        assert git_sha() == "cafe123"
        monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "   ")
        monkeypatch.setenv("GIT_SHA", "abc1234")
        assert git_sha() == "abc1234"


class TestDeploymentId:
    def test_none_when_unset(self, monkeypatch):
        _clear_sha_env(monkeypatch)
        assert deployment_id() is None

    def test_returns_railway_deployment_id(self, monkeypatch):
        _clear_sha_env(monkeypatch)
        monkeypatch.setenv("RAILWAY_DEPLOYMENT_ID", "dep_abc")
        assert deployment_id() == "dep_abc"


class TestPublicBuild:
    def test_includes_version_sha_and_optional_deployment(self, monkeypatch):
        _clear_sha_env(monkeypatch)
        monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "feedfacecafe")
        monkeypatch.setenv("RAILWAY_DEPLOYMENT_ID", "d-99")
        assert public_build() == {
            "version": API_VERSION,
            "git_sha": "feedfac",
            "deployment_id": "d-99",
        }
        assert API_VERSION == "0.1.0"


class TestHealthAndMetaExposeBuild:
    def test_health_includes_build_fields(self, monkeypatch):
        _clear_sha_env(monkeypatch)
        monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "bada55abcdef")
        monkeypatch.setenv("RAILWAY_DEPLOYMENT_ID", "deploy-1")
        with patch("api.routers.health.ping", new_callable=AsyncMock) as mock_ping:
            mock_ping.return_value = True
            client = TestClient(app)
            data = client.get("/health").json()
        assert data["version"] == "0.1.0"
        assert data["git_sha"] == "bada55a"
        assert data["deployment_id"] == "deploy-1"
        assert data["ok"] is True
        assert data["db"] == "up"

    def test_meta_includes_build_fields_and_defaults_locally(self, monkeypatch):
        _clear_sha_env(monkeypatch)
        client = TestClient(app)
        data = client.get("/meta").json()
        assert data["version"] == "0.1.0"
        assert data["git_sha"] == "dev"
        assert data["deployment_id"] is None
        assert data["name"] == "SafetyView API"
