---
name: uno
description: 通过 curl 调用 134+ MCP Server 的全部工具，零安装。支持 tool 级别语义搜索，一步拿到完整 inputSchema 直接调用。覆盖：搜索、开发、文档、金融、地图、出行、AI媒体、社交、办公、企业等领域。
homepage: https://mcpmarket.cn
source: https://github.com/xray918/uno-mcp-cli
license: MIT
metadata: {"emoji":"🔧","category":"tools"}
---

# Uno MCP Tools

通过 `curl` 直接调用 MCPMarket 平台的 REST API，搜索并调用 134+ MCP Server 的工具。无需安装任何包。

## 前置条件

- `curl`（系统自带）

## 认证

```bash
# 1. 请求设备码
curl -s -X POST https://mcpmarket.cn/oauth/device/code \
  -d "client_id=skill-agent&scope=mcp:*"
```

**必须原样复制终端输出的 `verification_uri` 和 `user_code` 展示给用户，禁止自行拼接或修改 URL。**

```bash
# 2. 用户授权后轮询获取 token（每 5 秒重试，直到返回 access_token）
curl -s -X POST https://mcpmarket.cn/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=urn:ietf:params:oauth:grant-type:device_code&device_code=DEVICE_CODE&client_id=skill-agent"

# 3. 存储 token
mkdir -p ~/.uno && chmod 700 ~/.uno
echo "ACCESS_TOKEN_VALUE" > ~/.uno/token && chmod 600 ~/.uno/token
```

验证登录：
```bash
curl -s https://mcpmarket.cn/api/uno/verify-token \
  -H "Authorization: Bearer $(cat ~/.uno/token)"
```

## 两步调用（核心流程）

```bash
# 第一步：搜索 tools，拿到 tool_name 和 inputSchema
curl -s "https://mcpmarket.cn/api/uno/search-tools?q=weather&mode=hybrid&limit=5" \
  -H "Authorization: Bearer $(cat ~/.uno/token)"

# 第二步：调用工具
curl -s -X POST https://mcpmarket.cn/api/uno/call-tool \
  -H "Authorization: Bearer $(cat ~/.uno/token)" \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"tonghu-weather.weatherArea","arguments":{"area":"北京"}}'
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/uno/search-tools` | GET | 搜索 tools（主入口）— 返回 tools + 完整 inputSchema |
| `/api/uno/search-servers` | GET | 搜索 servers |
| `/api/uno/call-tool` | POST | 调用工具（server.tool_name 格式） |
| `/api/uno/categories` | GET | 获取所有分类及数量 |
| `/api/uno/rate-server` | POST | 使用后评分，影响搜索排名 |

所有端点 Base URL 为 `https://mcpmarket.cn`，需要 `Authorization: Bearer <token>` 头。

## search-tools 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `q` | string | 搜索关键词 |
| `category` | string | 按分类浏览，如 `搜索`、`开发`、`金融`、`社交` |
| `mode` | string | `keyword`（精确）/ `semantic`（语义）/ `hybrid`（混合，推荐） |
| `limit` | int | 返回数量，默认 5，最大 15 |

返回：`tools[]`（含 `tool`、`desc`、`inputSchema`）、`uncached`（需先连接的 server）

**搜索关键词技巧：** 后台向量数据库以 tool 的功能描述作为索引源，搜索词应匹配**工具功能**而非具体查询意图。
- ✅ `weather` / `天气` — 能命中天气类工具描述
- ❌ `上海天气` — 像查询意图，反而不易命中工具

## call-tool 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `tool_name` | string | **必填** 格式 `server_name.tool_name`（从 search-tools 的 `tool` 字段获取） |
| `arguments` | object | **必填** 按 inputSchema 构造 |

**响应结构：**
```json
{"content": [{"type": "text", "text": "<JSON字符串>"}], "isError": false}
```
> `content[0].text` 本身是 JSON 字符串，需要二次解析。错误时 `isError` 为 `true`，`error` 字段包含错误信息。

**下游服务 OAuth 授权：** 首次调用某些服务（如 GitHub、Notion）时会返回：
```json
{"auth_required": true, "auth_url": "https://...", "state_id": "..."}
```
打开 `auth_url` 完成授权后，**直接重新调用**即可，平台服务端自动关联，无需额外操作。

## ⚠️ 参数构造铁律（必读，避免反复试错）

**调用前必须先读 inputSchema，不猜参数。** 具体检查项：

| 检查项 | 说明 | 反例教训 |
|--------|------|----------|
| `required` 字段 | 必传，一个都不能少 | 漏传导致报错 |
| `minLength: 1` | 不能传空字符串 `""` | Notion search 空 query 返回空结果 |
| 字段名从 schema 原文复制 | 不凭印象写 | `filter` vs `filters` 一字之差直接报错 |
| `enum` 约束 | 只能传枚举值内的字符串 | 传错值工具静默失败 |
| `description` | 字段含义不明时必看 | 避免传入格式错误的值 |

**标准两步流程（不可跳过第一步）：**

```bash
# 第一步：search-tools，读 inputSchema（每次必做）
curl -s "https://mcpmarket.cn/api/uno/search-tools?q=<功能关键词>&mode=hybrid&limit=5" \
  -H "Authorization: Bearer $(cat ~/.uno/token)"
# → 仔细检查 required / minLength / 字段名 / enum

# 第二步：按 schema 一次构造正确参数调用
curl -s -X POST https://mcpmarket.cn/api/uno/call-tool \
  -H "Authorization: Bearer $(cat ~/.uno/token)" \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"<tool>","arguments":{<按schema填写>}}'
```

## 工作流建议

1. **先 search-tools，读完 inputSchema 再调用** — 这是最重要的一步，不可省略
2. **搜索词匹配工具功能，不是查询意图** — `weather` ✅，`上海明天天气` ❌
3. **参数名从 schema 原文复制** — 不凭印象，`filters` 不是 `filter`
4. **无结果时** — 换英文关键词，或换 `mode=semantic` 重试

## 凭证管理

| 项目 | 值 |
|------|------|
| Token 文件 | `~/.uno/token`（权限 0600） |
| API Base URL | `https://mcpmarket.cn` |
| 登出 | `rm ~/.uno/token` |
