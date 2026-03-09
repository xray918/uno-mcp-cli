"""CLI entry point — maps MCP operations to bash commands."""

import asyncio
import json
import sys

import click

from . import client, oauth

DEFAULT_MCP_URL = "https://uno.mcpmarket.cn/mcp"


def _run(coro):
    return asyncio.run(coro)


def _output(data, as_json: bool):
    if as_json:
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    name = item.get("name", item.get("uri", ""))
                    desc = item.get("description", "")
                    click.echo(f"  {name}")
                    if desc:
                        click.echo(f"    {desc}")
                else:
                    click.echo(f"  {item}")
        elif isinstance(data, dict):
            click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            click.echo(str(data))


@click.group()
@click.option("--server", "-s", default=DEFAULT_MCP_URL, help="MCP server URL")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def main(ctx, server, as_json):
    """mcp-cli — Python CLI client for MCP servers with OAuth 2.1."""
    ctx.ensure_object(dict)
    ctx.obj["server"] = server
    ctx.obj["json"] = as_json


# ── Auth commands ──────────────────────────────────────────────


@main.command()
@click.option("--headless", is_flag=True, help="Device Code Flow (no browser needed, for server environments)")
@click.pass_context
def login(ctx, headless):
    """Authenticate with the MCP server via OAuth 2.1 + PKCE."""
    server = ctx.obj["server"]
    click.echo(f"Logging in to {server} ...")
    try:
        if headless:
            tokens = _run(oauth.login_device(server))
        else:
            tokens = _run(oauth.login(server))
        click.echo(f"Login successful! Token saved for {server}")
        if ctx.obj["json"]:
            safe = {k: v for k, v in tokens.items() if k != "access_token"}
            safe["access_token"] = tokens["access_token"][:12] + "..."
            _output(safe, True)
    except Exception as e:
        click.echo(f"Login failed: {e}", err=True)
        sys.exit(1)


@main.command()
@click.pass_context
def logout(ctx):
    """Remove stored credentials."""
    server = ctx.obj["server"]
    oauth.logout(server)
    click.echo(f"Logged out from {server}")


@main.command()
@click.pass_context
def status(ctx):
    """Check login status and server connectivity."""
    server = ctx.obj["server"]
    tokens = oauth.load_tokens(server)
    if not tokens:
        click.echo(f"Not logged in to {server}")
        sys.exit(1)

    click.echo(f"Logged in to {server}")
    click.echo(f"Testing connection...")
    ok = _run(client.ping(server))
    if ok:
        click.echo("Server is reachable ✓")
    else:
        click.echo("Server unreachable or token expired ✗")
        sys.exit(1)


# ── Tools commands ─────────────────────────────────────────────


@main.group(name="tools")
def tools_group():
    """Manage MCP tools."""
    pass


@tools_group.command(name="list")
@click.pass_context
def tools_list(ctx):
    """List all available tools on the server."""
    server = ctx.obj["server"]
    as_json = ctx.obj["json"]
    try:
        tools = _run(client.list_tools(server))
        if as_json:
            _output(tools, True)
        else:
            click.echo(f"Available tools ({len(tools)}):")
            _output(tools, False)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@tools_group.command(name="get")
@click.argument("tool_name")
@click.pass_context
def tools_get(ctx, tool_name):
    """Get the schema of a specific tool."""
    server = ctx.obj["server"]
    try:
        tool = _run(client.get_tool(server, tool_name))
        if tool:
            _output(tool, True)
        else:
            click.echo(f"Tool '{tool_name}' not found", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@tools_group.command(name="call")
@click.argument("tool_name")
@click.argument("arguments", default="{}")
@click.pass_context
def tools_call(ctx, tool_name, arguments):
    """Call a tool with JSON arguments.

    Example: mcp-cli tools call get_servers '{}'
    """
    server = ctx.obj["server"]
    try:
        args = json.loads(arguments)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON arguments: {e}", err=True)
        sys.exit(1)

    try:
        result = _run(client.call_tool(server, tool_name, args))
        _output(result, True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# ── Resources commands ─────────────────────────────────────────


@main.group(name="resources")
def resources_group():
    """Manage MCP resources."""
    pass


@resources_group.command(name="list")
@click.pass_context
def resources_list(ctx):
    """List all available resources."""
    server = ctx.obj["server"]
    as_json = ctx.obj["json"]
    try:
        resources = _run(client.list_resources(server))
        if as_json:
            _output(resources, True)
        else:
            click.echo(f"Available resources ({len(resources)}):")
            _output(resources, False)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# ── Prompts commands ───────────────────────────────────────────


@main.group(name="prompts")
def prompts_group():
    """Manage MCP prompts."""
    pass


@prompts_group.command(name="list")
@click.pass_context
def prompts_list(ctx):
    """List all available prompts."""
    server = ctx.obj["server"]
    as_json = ctx.obj["json"]
    try:
        prompts = _run(client.list_prompts(server))
        if as_json:
            _output(prompts, True)
        else:
            click.echo(f"Available prompts ({len(prompts)}):")
            _output(prompts, False)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
