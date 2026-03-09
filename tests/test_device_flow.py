"""Unit tests for Device Code Flow (RFC 8628) — client side."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_cli import oauth
from mcp_cli.config import TOKEN_FILE


@pytest.fixture
def mock_oauth_metadata():
    return {
        "resource_server": "https://example.com",
        "authorization_server": "https://example.com",
        "authorization_endpoint": "https://example.com/oauth/authorize",
        "token_endpoint": "https://example.com/oauth/token",
        "registration_endpoint": "https://example.com/oauth/register",
        "device_authorization_endpoint": "https://example.com/oauth/device/code",
        "scopes_supported": ["mcp:*"],
    }


@pytest.fixture
def mock_device_response():
    return {
        "device_code": "test-device-code-abc123",
        "user_code": "WDJB-MPFK",
        "verification_uri": "https://example.com/oauth/device",
        "verification_uri_complete": "https://example.com/oauth/device?user_code=WDJB-MPFK",
        "expires_in": 600,
        "interval": 1,
    }


@pytest.fixture
def mock_token_response():
    return {
        "access_token": "test-access-token-xyz789",
        "token_type": "Bearer",
        "expires_in": 2592000,
        "scope": "mcp:*",
    }


class TestDiscoverDeviceEndpoint:
    def test_metadata_includes_device_endpoint(self, mock_oauth_metadata):
        assert mock_oauth_metadata["device_authorization_endpoint"] is not None

    def test_metadata_without_device_endpoint(self):
        meta = {
            "resource_server": "https://example.com",
            "device_authorization_endpoint": None,
        }
        assert meta["device_authorization_endpoint"] is None


class TestLoginDevice:
    @pytest.mark.asyncio
    async def test_raises_when_no_device_endpoint(self):
        meta_no_device = {
            "resource_server": "https://example.com",
            "authorization_server": "https://example.com",
            "authorization_endpoint": "https://example.com/oauth/authorize",
            "token_endpoint": "https://example.com/oauth/token",
            "registration_endpoint": "https://example.com/oauth/register",
            "device_authorization_endpoint": None,
            "scopes_supported": ["mcp:*"],
        }

        with patch.object(oauth, "discover_oauth_metadata", return_value=meta_no_device):
            with pytest.raises(RuntimeError, match="does not support Device Code Flow"):
                await oauth.login_device("https://example.com/mcp")

    @pytest.mark.asyncio
    async def test_raises_when_no_registration_endpoint(self):
        meta = {
            "resource_server": "https://example.com",
            "authorization_server": "https://example.com",
            "authorization_endpoint": "https://example.com/oauth/authorize",
            "token_endpoint": "https://example.com/oauth/token",
            "registration_endpoint": None,
            "device_authorization_endpoint": "https://example.com/oauth/device/code",
            "scopes_supported": ["mcp:*"],
        }

        with patch.object(oauth, "discover_oauth_metadata", return_value=meta):
            with pytest.raises(RuntimeError, match="dynamic client registration"):
                await oauth.login_device("https://example.com/mcp")

    @pytest.mark.asyncio
    async def test_successful_device_flow(
        self, mock_oauth_metadata, mock_device_response, mock_token_response, tmp_path
    ):
        """Full device flow: discover → register → device code → poll → token."""

        call_count = {"token_polls": 0}

        def make_mock_response(status_code, json_data):
            resp = MagicMock()
            resp.status_code = status_code
            resp.json.return_value = json_data
            resp.raise_for_status = MagicMock()
            return resp

        class FakeAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, **kwargs):
                if "/device/code" in url:
                    return make_mock_response(200, mock_device_response)
                if "/token" in url:
                    call_count["token_polls"] += 1
                    if call_count["token_polls"] < 3:
                        return make_mock_response(400, {"error": "authorization_pending"})
                    return make_mock_response(200, mock_token_response)
                if "/register" in url:
                    return make_mock_response(201, {"client_id": "test-client-id"})
                raise ValueError(f"Unexpected URL: {url}")

            async def get(self, url, **kwargs):
                raise ValueError(f"Unexpected GET: {url}")

        token_file = tmp_path / "tokens.json"

        with (
            patch.object(oauth, "discover_oauth_metadata", return_value=mock_oauth_metadata),
            patch.object(oauth, "register_client", return_value={"client_id": "test-client-id"}),
            patch("httpx.AsyncClient", return_value=FakeAsyncClient()),
            patch("mcp_cli.oauth.save_tokens") as mock_save,
        ):
            result = await oauth.login_device("https://example.com/mcp")

        assert result["access_token"] == "test-access-token-xyz789"
        assert result["client_id"] == "test-client-id"
        assert result["mcp_url"] == "https://example.com/mcp"
        assert call_count["token_polls"] == 3
        mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_device_flow_access_denied(
        self, mock_oauth_metadata, mock_device_response
    ):
        def make_mock_response(status_code, json_data):
            resp = MagicMock()
            resp.status_code = status_code
            resp.json.return_value = json_data
            resp.raise_for_status = MagicMock()
            return resp

        class FakeAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, **kwargs):
                if "/device/code" in url:
                    return make_mock_response(200, mock_device_response)
                if "/token" in url:
                    return make_mock_response(400, {"error": "access_denied"})
                if "/register" in url:
                    return make_mock_response(201, {"client_id": "test-client-id"})
                raise ValueError(f"Unexpected URL: {url}")

        with (
            patch.object(oauth, "discover_oauth_metadata", return_value=mock_oauth_metadata),
            patch.object(oauth, "register_client", return_value={"client_id": "test-client-id"}),
            patch("httpx.AsyncClient", return_value=FakeAsyncClient()),
            patch("mcp_cli.oauth.save_tokens"),
        ):
            with pytest.raises(RuntimeError, match="拒绝"):
                await oauth.login_device("https://example.com/mcp")

    @pytest.mark.asyncio
    async def test_device_flow_expired(
        self, mock_oauth_metadata, mock_device_response
    ):
        def make_mock_response(status_code, json_data):
            resp = MagicMock()
            resp.status_code = status_code
            resp.json.return_value = json_data
            resp.raise_for_status = MagicMock()
            return resp

        class FakeAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, **kwargs):
                if "/device/code" in url:
                    return make_mock_response(200, mock_device_response)
                if "/token" in url:
                    return make_mock_response(400, {"error": "expired_token"})
                if "/register" in url:
                    return make_mock_response(201, {"client_id": "test-client-id"})
                raise ValueError(f"Unexpected URL: {url}")

        with (
            patch.object(oauth, "discover_oauth_metadata", return_value=mock_oauth_metadata),
            patch.object(oauth, "register_client", return_value={"client_id": "test-client-id"}),
            patch("httpx.AsyncClient", return_value=FakeAsyncClient()),
            patch("mcp_cli.oauth.save_tokens"),
        ):
            with pytest.raises(RuntimeError, match="过期"):
                await oauth.login_device("https://example.com/mcp")


class TestCLIHeadlessFlag:
    def test_login_help_shows_headless(self):
        """Verify --headless flag appears in login command help."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "mcp_cli.cli", "login", "--help"],
            capture_output=True, text=True,
        )
        assert "--headless" in result.stdout
        assert "Device Code Flow" in result.stdout
