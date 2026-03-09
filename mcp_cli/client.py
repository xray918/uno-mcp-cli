"""MCP client wrapper — connects to remote MCP server over StreamableHTTP."""

import json
from contextlib import asynccontextmanager
from typing import Any

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from .oauth import get_valid_token


class _BearerAuth(httpx.Auth):
    def __init__(self, token: str):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        request.headers.setdefault("User-Agent", "mcp-bash-cli/0.1.0")
        yield request


@asynccontextmanager
async def connect(mcp_url: str):
    """Yield an initialized MCP ClientSession with OAuth bearer token."""
    token = await get_valid_token(mcp_url)
    auth = _BearerAuth(token)

    async with streamablehttp_client(
        url=mcp_url,
        auth=auth,
        headers={"User-Agent": "mcp-bash-cli/0.1.0"},
    ) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


async def list_tools(mcp_url: str) -> list[dict]:
    async with connect(mcp_url) as session:
        result = await session.list_tools()
        return [
            {
                "name": t.name,
                "description": t.description or "",
            }
            for t in result.tools
        ]


async def get_tool(mcp_url: str, tool_name: str) -> dict | None:
    async with connect(mcp_url) as session:
        result = await session.list_tools()
        for t in result.tools:
            if t.name == tool_name:
                return {
                    "name": t.name,
                    "description": t.description or "",
                    "inputSchema": t.inputSchema if hasattr(t, "inputSchema") else {},
                }
        return None


async def call_tool(mcp_url: str, tool_name: str, arguments: dict[str, Any]) -> dict:
    async with connect(mcp_url) as session:
        result = await session.call_tool(tool_name, arguments)
        contents = []
        for c in result.content:
            if hasattr(c, "text"):
                contents.append({"type": "text", "text": c.text})
            else:
                contents.append({"type": str(c.type), "data": str(c)})
        return {
            "isError": result.isError if hasattr(result, "isError") else False,
            "content": contents,
        }


async def list_resources(mcp_url: str) -> list[dict]:
    async with connect(mcp_url) as session:
        result = await session.list_resources()
        return [
            {
                "uri": str(r.uri),
                "name": r.name or "",
                "description": r.description or "" if hasattr(r, "description") else "",
            }
            for r in result.resources
        ]


async def list_prompts(mcp_url: str) -> list[dict]:
    async with connect(mcp_url) as session:
        result = await session.list_prompts()
        return [
            {
                "name": p.name,
                "description": p.description or "",
            }
            for p in result.prompts
        ]


async def ping(mcp_url: str) -> bool:
    try:
        async with connect(mcp_url) as session:
            await session.send_ping()
            return True
    except Exception:
        return False
