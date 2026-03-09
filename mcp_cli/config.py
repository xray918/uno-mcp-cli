"""Token storage and configuration management."""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".uno"
TOKEN_FILE = CONFIG_DIR / "tokens.json"


def ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_tokens(server_url: str, tokens: dict) -> None:
    ensure_config_dir()
    all_tokens = load_all_tokens()
    all_tokens[server_url] = tokens
    TOKEN_FILE.write_text(json.dumps(all_tokens, indent=2, ensure_ascii=False))


def load_tokens(server_url: str) -> dict | None:
    all_tokens = load_all_tokens()
    return all_tokens.get(server_url)


def load_all_tokens() -> dict:
    if not TOKEN_FILE.exists():
        return {}
    try:
        return json.loads(TOKEN_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def clear_tokens(server_url: str) -> None:
    all_tokens = load_all_tokens()
    all_tokens.pop(server_url, None)
    ensure_config_dir()
    TOKEN_FILE.write_text(json.dumps(all_tokens, indent=2, ensure_ascii=False))
