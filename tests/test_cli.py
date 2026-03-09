"""Integration tests for mcp-bash-cli — requires a valid OAuth token."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).parent.parent
MCP_URL = "https://uno.mcpmarket.cn/mcp"


def run_mcpx(*args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "mcp_cli.cli", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
        timeout=timeout,
    )


def run_mcpx_json(*args: str, timeout: int = 30) -> dict | list:
    result = run_mcpx("--json", *args, timeout=timeout)
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


# ── Auth tests ──────────────────────────────────────────────────


class TestAuth:
    def test_status_shows_logged_in(self):
        result = run_mcpx("status")
        assert result.returncode == 0
        assert "Logged in" in result.stdout

    def test_status_server_reachable(self):
        result = run_mcpx("status")
        assert "reachable" in result.stdout


# ── Tools discovery tests ──────────────────────────────────────


class TestToolsDiscovery:
    def test_list_tools_returns_array(self):
        data = run_mcpx_json("tools", "list")
        assert isinstance(data, list)
        assert len(data) >= 3
        names = {t["name"] for t in data}
        assert "uno_discover_servers" in names
        assert "uno_call_tool" in names
        assert "uno_execute_script" in names

    def test_get_tool_schema(self):
        result = run_mcpx("tools", "get", "uno_call_tool")
        assert result.returncode == 0
        schema = json.loads(result.stdout)
        assert schema["name"] == "uno_call_tool"
        assert "inputSchema" in schema

    def test_get_nonexistent_tool(self):
        result = run_mcpx("tools", "get", "nonexistent_tool_xyz")
        assert result.returncode == 1


# ── Uno discover servers tests ─────────────────────────────────


class TestUnoDiscover:
    def test_discover_time_server(self):
        data = run_mcpx_json(
            "tools", "call", "uno_discover_servers",
            '{"server_names": ["time"]}',
        )
        assert data["isError"] is False
        inner = json.loads(data["content"][0]["text"])
        assert "time" in inner["servers"]
        tool_names = [t["name"] for t in inner["servers"]["time"]["tools"]]
        assert "get_current_time" in tool_names
        assert "convert_time" in tool_names


# ── Uno call tool tests ────────────────────────────────────────


class TestUnoCallTool:
    def test_get_current_time(self):
        data = run_mcpx_json(
            "tools", "call", "uno_call_tool",
            '{"tool_name": "time.get_current_time", "arguments": {"timezone": "Asia/Shanghai"}}',
        )
        assert data["isError"] is False
        inner = json.loads(data["content"][0]["text"])
        assert inner["success"] is True
        result_text = inner["result"]["content"][0]["text"]
        time_data = json.loads(result_text)
        assert time_data["timezone"] == "Asia/Shanghai"
        assert "datetime" in time_data

    def test_convert_time(self):
        data = run_mcpx_json(
            "tools", "call", "uno_call_tool",
            json.dumps({
                "tool_name": "time.convert_time",
                "arguments": {
                    "source_timezone": "Asia/Shanghai",
                    "time": "12:00",
                    "target_timezone": "America/New_York",
                },
            }),
        )
        assert data["isError"] is False
        inner = json.loads(data["content"][0]["text"])
        assert inner["success"] is True


# ── Execute script tests ───────────────────────────────────────


class TestExecuteScript:
    def test_python_script(self):
        data = run_mcpx_json(
            "tools", "call", "uno_execute_script",
            '{"language": "python", "script": "print(42 * 2)"}',
        )
        assert data["isError"] is False
        inner = json.loads(data["content"][0]["text"])
        assert inner["success"] is True
        assert "84" in inner["stdout"]

    def test_bash_script(self):
        data = run_mcpx_json(
            "tools", "call", "uno_execute_script",
            '{"language": "bash", "script": "echo hello-mcp"}',
        )
        assert data["isError"] is False
        inner = json.loads(data["content"][0]["text"])
        assert inner["success"] is True
        assert "hello-mcp" in inner["stdout"]
