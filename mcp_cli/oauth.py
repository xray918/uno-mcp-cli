"""OAuth 2.1 + PKCE authentication flow for MCP servers."""

import asyncio
import base64
import hashlib
import json
import secrets
import time
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from .config import clear_tokens, load_tokens, save_tokens

CALLBACK_PORT = 9876
CALLBACK_PATH = "/callback"
REDIRECT_URI = f"http://localhost:{CALLBACK_PORT}{CALLBACK_PATH}"
HTTP_HEADERS = {"User-Agent": "mcp-bash-cli/0.1.0"}


def _generate_pkce() -> tuple[str, str]:
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


async def discover_oauth_metadata(mcp_url: str) -> dict:
    """Discover OAuth endpoints from the MCP server's well-known URLs."""
    parsed = urlparse(mcp_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    async with httpx.AsyncClient(follow_redirects=True, headers=HTTP_HEADERS) as client:
        prm_url = f"{base_url}/.well-known/oauth-protected-resource"
        resp = await client.get(prm_url)
        resp.raise_for_status()
        prm = resp.json()

        auth_server = prm["authorization_servers"][0]
        as_url = f"{auth_server}/.well-known/oauth-authorization-server"
        resp = await client.get(as_url)
        resp.raise_for_status()
        as_meta = resp.json()

    return {
        "resource_server": base_url,
        "authorization_server": auth_server,
        "authorization_endpoint": as_meta["authorization_endpoint"],
        "token_endpoint": as_meta["token_endpoint"],
        "registration_endpoint": as_meta.get("registration_endpoint"),
        "device_authorization_endpoint": as_meta.get("device_authorization_endpoint"),
        "scopes_supported": as_meta.get("scopes_supported", []),
    }


async def register_client(registration_endpoint: str) -> dict:
    """Dynamic client registration (RFC 7591)."""
    payload = {
        "client_name": "Uno",
        "redirect_uris": [REDIRECT_URI],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
    }
    async with httpx.AsyncClient(follow_redirects=True, headers=HTTP_HEADERS) as client:
        resp = await client.post(registration_endpoint, json=payload)
        resp.raise_for_status()
        return resp.json()


class _CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler that captures the OAuth callback."""

    auth_code: str | None = None
    state: str | None = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != CALLBACK_PATH:
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)
        _CallbackHandler.auth_code = params.get("code", [None])[0]
        _CallbackHandler.state = params.get("state", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h2>Authorization successful!</h2>"
            b"<p>You can close this tab now.</p></body></html>"
        )

    def log_message(self, format, *args):
        pass  # suppress logs


async def login(mcp_url: str) -> dict:
    """Full OAuth 2.1 + PKCE login flow. Returns token dict."""
    meta = await discover_oauth_metadata(mcp_url)

    # Dynamic client registration
    if not meta.get("registration_endpoint"):
        raise RuntimeError("Server does not support dynamic client registration")
    reg = await register_client(meta["registration_endpoint"])
    client_id = reg["client_id"]

    # PKCE
    code_verifier, code_challenge = _generate_pkce()
    state = secrets.token_urlsafe(32)

    # Build authorization URL
    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if meta["scopes_supported"]:
        auth_params["scope"] = " ".join(meta["scopes_supported"])

    auth_url = f"{meta['authorization_endpoint']}?{urlencode(auth_params)}"

    # Start local callback server
    _CallbackHandler.auth_code = None
    _CallbackHandler.state = None
    server = HTTPServer(("localhost", CALLBACK_PORT), _CallbackHandler)
    server_thread = threading.Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    # Open browser
    print(f"Opening browser for authorization...", flush=True)
    print(f"If browser doesn't open, visit:\n{auth_url}", flush=True)
    webbrowser.open(auth_url)

    # Wait for callback
    server_thread.join(timeout=120)
    server.server_close()

    if not _CallbackHandler.auth_code:
        raise RuntimeError("No authorization code received (timeout or denied)")

    if _CallbackHandler.state != state:
        raise RuntimeError("State mismatch — possible CSRF attack")

    # Exchange code for token (with retry)
    token_data = {
        "grant_type": "authorization_code",
        "code": _CallbackHandler.auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "code_verifier": code_verifier,
    }
    print(f"Exchanging authorization code for token...", flush=True)
    tokens = None
    last_error = None
    async with httpx.AsyncClient(follow_redirects=True, timeout=30, headers=HTTP_HEADERS) as http:
        for attempt in range(3):
            try:
                resp = await http.post(meta["token_endpoint"], data=token_data)
                if resp.status_code >= 500:
                    last_error = f"Server error {resp.status_code}: {resp.text}"
                    print(f"  Attempt {attempt + 1}/3 failed ({resp.status_code}), retrying...", flush=True)
                    await asyncio.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                tokens = resp.json()
                break
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Token exchange failed: {e}")
            except httpx.RequestError as e:
                last_error = str(e)
                print(f"  Attempt {attempt + 1}/3 network error, retrying...", flush=True)
                await asyncio.sleep(2 ** attempt)

    if tokens is None:
        raise RuntimeError(f"Token exchange failed after 3 attempts: {last_error}")

    # Persist
    token_record = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "token_type": tokens.get("token_type", "Bearer"),
        "client_id": client_id,
        "mcp_url": mcp_url,
        "authorization_server": meta["authorization_server"],
        "token_endpoint": meta["token_endpoint"],
    }
    save_tokens(mcp_url, token_record)
    return token_record


async def login_device(mcp_url: str) -> dict:
    """Device Code Flow login for headless/server environments (RFC 8628)."""
    meta = await discover_oauth_metadata(mcp_url)

    device_endpoint = meta.get("device_authorization_endpoint")
    if not device_endpoint:
        raise RuntimeError(
            "Server does not support Device Code Flow. "
            "Use browser-based login instead."
        )

    if not meta.get("registration_endpoint"):
        raise RuntimeError("Server does not support dynamic client registration")
    reg = await register_client(meta["registration_endpoint"])
    client_id = reg["client_id"]

    scope = " ".join(meta["scopes_supported"]) if meta["scopes_supported"] else "mcp:*"

    async with httpx.AsyncClient(follow_redirects=True, headers=HTTP_HEADERS) as client:
        resp = await client.post(device_endpoint, data={
            "client_id": client_id,
            "scope": scope,
        })
        resp.raise_for_status()
        device_data = resp.json()

    user_code = device_data["user_code"]
    verification_uri = device_data["verification_uri"]
    verification_uri_complete = device_data.get("verification_uri_complete", "")
    expires_in = device_data.get("expires_in", 600)
    interval = device_data.get("interval", 5)

    print(f"\n{'=' * 56}", flush=True)
    print(f"  请在浏览器中打开以下链接并输入设备码:", flush=True)
    print(f"  链接: {verification_uri}", flush=True)
    print(f"  设备码: {user_code}", flush=True)
    if verification_uri_complete:
        print(f"\n  或直接打开: {verification_uri_complete}", flush=True)
    print(f"\n  等待授权中... (有效期 {expires_in // 60} 分钟)", flush=True)
    print(f"{'=' * 56}\n", flush=True)

    token_endpoint = meta["token_endpoint"]
    grant_type = "urn:ietf:params:oauth:grant-type:device_code"
    tokens = None

    async with httpx.AsyncClient(
        follow_redirects=True, timeout=30, headers=HTTP_HEADERS
    ) as http:
        start = time.time()
        while time.time() - start < expires_in:
            await asyncio.sleep(interval)

            try:
                resp = await http.post(token_endpoint, data={
                    "grant_type": grant_type,
                    "device_code": device_data["device_code"],
                    "client_id": client_id,
                })

                if resp.status_code == 200:
                    tokens = resp.json()
                    break

                error_data = resp.json()
                error = error_data.get("error", "")

                if error == "authorization_pending":
                    continue
                elif error == "slow_down":
                    interval += 5
                    continue
                elif error == "access_denied":
                    raise RuntimeError("用户拒绝了授权")
                elif error == "expired_token":
                    raise RuntimeError("设备码已过期，请重新发起登录")
                else:
                    raise RuntimeError(f"Token 请求失败: {error_data}")

            except httpx.RequestError:
                print("  网络错误，重试中...", flush=True)
                await asyncio.sleep(interval)

    if tokens is None:
        raise RuntimeError("等待授权超时，请重新发起登录")

    token_record = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "token_type": tokens.get("token_type", "Bearer"),
        "client_id": client_id,
        "mcp_url": mcp_url,
        "authorization_server": meta["authorization_server"],
        "token_endpoint": meta["token_endpoint"],
    }
    save_tokens(mcp_url, token_record)
    return token_record


async def get_valid_token(mcp_url: str) -> str:
    """Get a valid access token, refreshing if needed."""
    record = load_tokens(mcp_url)
    if not record:
        raise RuntimeError(f"Not logged in. Run: mcp-cli login {mcp_url}")
    return record["access_token"]


def logout(mcp_url: str) -> None:
    clear_tokens(mcp_url)
