# uno-cli

通过 bash 命令调用 Uno MCP 网关聚合的 80+ MCP Server，无需 LLM 原生 tool_use。

## 安装

```bash
pip install uno-cli
```

## 认证

服务器环境（无浏览器）使用 Device Code Flow：

```bash
mcpx login --headless
```

终端会输出设备码和验证链接，在任意浏览器中打开链接、输入设备码完成授权。Token 存储在 `~/.uno/tokens.json`。

## 使用

```bash
# 检查状态
mcpx status

# 发现 server 工具
mcpx tools call uno_discover_servers '{"server_names": ["time"]}'

# 调用工具
mcpx tools call uno_call_tool '{"tool_name": "time.get_current_time", "arguments": {"timezone": "Asia/Shanghai"}}'

# 沙盒执行脚本
mcpx tools call uno_execute_script '{"language": "python", "script": "print(2**10)"}'
```

## 支持的 MCP Server

Uno 网关聚合了 80+ MCP Server，涵盖搜索、GitHub、文档、图表、金融、地图、出行等场景。详见 [SKILL.md](https://mcpmarket.cn/skill.md)。

## MCP 网关

`https://uno.mcpmarket.cn/mcp`
