---
name: uno
description: 通过 bash 命令调用 80+ MCP Server 的全部工具，无需 LLM 原生 tool_use。覆盖以下所有类别：搜索与信息检索（DuckDuckGo/Brave/Bing/Exa/Perplexity/Google News/趋势聚合）、开发工具（GitHub/Context7/Figma/Sentry/Neon/Supabase/n8n/HuggingFace）、文档与内容（Markitdown/Fetch/Firecrawl/Word/Excel/PowerPoint/Notion/arXiv）、数据可视化（AntV图表/ECharts/PPT生成）、金融数据（A股/东方财富/雅虎财经/Alpha Vantage/加密货币）、时间与地图（全球时区/百度地图/Google地图）、出行与生活（12306/航班/滴滴/酒店/菜谱/麦当劳/油价/快递）、AI与媒体（图像生成/语音合成/视觉理解/推理）、社交与社区（Reddit/HN/Slack/ClawdChat/抖音）、企业数据（工商/三要素认证/VIN查询/域名）、沙盒脚本执行（Python/Bash/Node）。使用场景：需要搜索网络、操作 GitHub、生成图表、查询地图/天气/股票/航班、执行代码、处理文档、调用任意外部工具时使用此 Skill。
homepage: https://mcpmarket.cn
metadata: {"emoji":"🔧","category":"tools","gateway":"https://uno.mcpmarket.cn/mcp"}
---

# Uno MCP Tools

通过 `mcpx` 命令行工具，调用 Uno 网关聚合的 80+ MCP Server。一条 bash 命令 = 一次工具调用。

## 安装

```bash
pip install uno-cli
```

安装后可用命令：`mcpx`

验证：`mcpx --help`

如果 `pip` 不可用，尝试 `pip3` 或先安装 Python 3.12+。

## 认证

首次使用需登录。服务器环境（无浏览器）使用 Device Code Flow：

```bash
mcpx login --headless
```

终端会输出设备码和链接，在任意浏览器中打开链接、输入设备码、选择 GitHub/Google/微信登录即可。终端自动完成。

Token 存储在 `~/.uno/tokens.json`，登录一次长期有效（30 天）。

检查状态：`mcpx status`

## 核心命令

```bash
# 列出网关工具（3 个入口工具）
mcpx --json tools list

# 发现目标 server 的工具
mcpx tools call uno_discover_servers '{"server_names": ["time"]}'

# 调用具体工具（格式：server.tool_name）
mcpx tools call uno_call_tool '{"tool_name": "time.get_current_time", "arguments": {"timezone": "Asia/Shanghai"}}'

# 沙盒执行脚本
mcpx tools call uno_execute_script '{"language": "python", "script": "print(2**10)"}'
```

所有输出为 JSON，可配合 `jq` 提取：

```bash
mcpx --json tools call uno_call_tool '{"tool_name": "time.get_current_time", "arguments": {"timezone": "UTC"}}' | jq '.content[0].text | fromjson'
```

## 两步调用模式

Uno 是网关，调用任何工具都是两步：

**第一步 — discover**：获取目标 server 的工具列表和参数 schema

```bash
mcpx tools call uno_discover_servers '{"server_names": ["github"]}'
```

**第二步 — call_tool**：用 `server.tool_name` 格式调用

```bash
mcpx tools call uno_call_tool '{"tool_name": "github.search_repositories", "arguments": {"query": "mcp server language:python"}}'
```

## 可用 Server 目录

以下是 Uno 网关当前聚合的全部 MCP Server。`server_names` 参数必须从此列表选择。

### 搜索与信息检索

| server | 说明 |
|--------|------|
| duckduckgo | 网页搜索 + URL 内容提取 |
| brave-search | Brave 搜索，支持 Web 和本地搜索 |
| exa-search | 神经搜索，适合代码和技术文档 |
| bing-search | 必应搜索，中文优化，无需 API Key |
| bocha-search-mcp | 博查搜索，覆盖数十亿网页 |
| metaso-search | 秘塔搜索，RAG 智能问答 + 网页提取 |
| perplexity-ask | Perplexity AI 搜索 |
| brightdata-search | 穿透反爬的实时网页数据采集 |
| Bright Data Search | 绕过反爬获取最新网页数据 |
| google-news | Google News 分类新闻搜索 |
| trends | 趋势聚合，20+ 热搜源 |

### 开发工具

| server | 说明 |
|--------|------|
| github | GitHub 仓库、Issue、PR 操作 |
| context7 | 实时代码库文档查询，防止 AI 幻觉 |
| ref-tools-mcp | 最新技术文档访问 |
| zread | GitHub 开源项目文档和代码分析 |
| figma-context | Figma 设计稿转代码 |
| sentry-mcp | Sentry 错误调试 |
| mcp-server-neon | Neon Postgres 数据库自然语言交互 |
| supabase-mcp | Supabase 项目 AI 管理 |
| n8n | n8n 工作流自动化 |
| hf-mcp-server | Hugging Face 模型服务 |
| MCP服务器开发工具包 | FastMCP 开发指南和模板 |

### 文档与内容

| server | 说明 |
|--------|------|
| markitdown | 任意 URI 转 Markdown |
| fetch | 网页转 Markdown，支持分页 |
| firecrawl | 网站爬取转结构化数据 |
| word | 创建和编辑 Word 文档 |
| excel | 创建/读取 Excel，含公式和图表 |
| powerpoint | PowerPoint 操作，32 个工具 |
| arxiv | arXiv 论文搜索和下载 |
| Arxiv-Paper-MCP | arXiv 论文搜索、解读、最新 AI 论文 |
| notion | Notion 页面和数据库管理 |
| pageindex-mcp | 基于推理的层级 RAG 系统 |

### 数据可视化

| server | 说明 |
|--------|------|
| chart | AntV 25+ 专业图表生成 |
| 图表生成工具 | ECharts 动态图表（折线/柱状/饼图/雷达/散点） |
| gezhe-ppt-mcp | 从主题生成 PPT |

### 金融与数据

| server | 说明 |
|--------|------|
| akshare-stock-china | A 股实时行情、K 线、财报 |
| eastmoney-stock-china | 东方财富 A 股数据和技术指标 |
| yahoo-finance | 雅虎财经全球股票行情 |
| Alpha Vantage | 全球金融数据（股票/加密/外汇/商品） |
| Qieman | 基金数据和投资分析 |
| dexpaprika | 加密货币和 DEX 实时数据 |
| 基金知识查询服务器 | 基金知识检索和股票搜索 |
| 货币与石油价格服务器 | 实时汇率和布伦特原油价格 |
| world-bank | 世界银行全球经济社会数据 |

### 时间与地图

| server | 说明 |
|--------|------|
| time | 全球时区查询和时间转换 |
| baidu-map | 百度地图 LBS 地理空间 API |
| google-map | Google 地图服务 |

### 出行与生活

| server | 说明 |
|--------|------|
| 12306 | 中国铁路车票查询 |
| variflight | 航班信息、天气、舒适度指标 |
| didi | 滴滴打车查价、预估时间、叫车 |
| Hotel MCP | 国内酒店查询（覆盖 80% 五星级） |
| aigohotel | 全球酒店搜索和推荐 |
| HowToCook-mcp | 菜谱和膳食规划 |
| McDonald's | 麦当劳活动日历和优惠券 |
| 美味不用等 | 排队取号服务 |
| today-oil-price-china | 全国 31 省油价实时查询 |
| express-tracking-china | 全球快递追踪（1000+ 物流商） |

### AI 与媒体

| server | 说明 |
|--------|------|
| minimax | MiniMax AI 决策优化 |
| elevenlabs | ElevenLabs 语音合成 |
| nano-banana | Gemini 图片生成 + ImgBB 托管 |
| modelscope-image | ModelScope AI 图像生成和变换 |
| zhipu-vision | 智谱视觉理解（图像分析/OCR/视频） |
| sequentialthinking | 结构化逐步推理 |
| edgeone-pages-mcp | HTML 部署到 EdgeOne Pages |

### 社交与社区

| server | 说明 |
|--------|------|
| reddit | Reddit 帖子、评论、趋势浏览 |
| mcp-hn | Hacker News 故事和用户 |
| slack | Slack 消息和频道管理 |
| clawdchat-mcp | ClawdChat AI 社交网络 |
| 🦐虾聊AI社交网络 | 虾聊 AI 社交（AI-to-AI） |
| douyin | 抖音无水印视频下载和音频提取 |

### 企业与数据服务

| server | 说明 |
|--------|------|
| enterprise-big-data-china | 中国企业工商、法务、财报、知产 |
| china-carrier-tri-factor-auth | 运营商三要素实名认证 |
| car-vin-lookup-china | VIN 车辆识别码查询 |
| 域名查询服务 | RDAP/WHOIS/DNS 域名信息 |
| 智能搜索工具集 | 14 个增强搜索覆盖主流技术平台 |
| apify-mcp-server | Apify 网页抓取任务管理 |
| mcp | Hyperbrowser 数据爬取 |
| BrightData | 浏览器自动化和页面操作 |
| GoogleDrive | Google Drive 文件管理 |
| Icons8 MCP server | SVG/PNG 图标获取 |
| Logo提取处理工具 | 网站 Logo 提取和分析 |
| Webhook MCP | 自定义 Webhook 请求 |
| 测试沙盒Sandbox MCP | 企业可恢复沙盒环境 |

### 其他特色服务

| server | 说明 |
|--------|------|
| bazi | 八字命理分析 |
| 星座 MCP 服务 | 星座查询、运势、配对 |
| MBTI测试服务 | MBTI 性格测试 |
| AI人格服务器 | 多 AI 角色协作 |
| biomcp | 生物医学 AI 工具包 |
| baichuan-mcp-servers | 百川智能医疗信息 |
| Theta Health MCP | HIPAA 健康数据（300+ 设备） |
| 苹果开发者文档搜索服务 | Apple 开发文档搜索 |
| taoke-mcp | 淘客推广链接转换（淘宝/京东/拼多多） |
| agentsyun-coupons-china | 外卖/娱乐/出行优惠券 |
| GoWeb3 Data | Web3 事件和新闻 |
| OSRS玩家数据服务 | 老学校 RuneScape 玩家数据 |
| 柏林公共服务查询服务 | 柏林 1000+ 行政服务查询 |
| 英国国家统计局MCP服务器 | 英国官方统计数据 |

## 常见用法示例

### 搜索网页

```bash
mcpx tools call uno_discover_servers '{"server_names": ["duckduckgo"]}'
mcpx tools call uno_call_tool '{"tool_name": "duckduckgo.search", "arguments": {"query": "MCP protocol 2025"}}'
```

### 操作 GitHub

```bash
mcpx tools call uno_discover_servers '{"server_names": ["github"]}'
mcpx tools call uno_call_tool '{"tool_name": "github.search_repositories", "arguments": {"query": "mcp server stars:>100"}}'
```

### 生成图表

```bash
mcpx tools call uno_discover_servers '{"server_names": ["chart"]}'
mcpx tools call uno_call_tool '{"tool_name": "chart.bindbindbindbindbindbindbar_bindchart", "arguments": {...}}'
```

注意：先用 discover 获取工具的 inputSchema，再按 schema 传参。

### 执行 Python 脚本

```bash
mcpx tools call uno_execute_script '{"language": "python", "script": "import json; print(json.dumps({\"result\": 42}))"}'
```

### 查询 A 股

```bash
mcpx tools call uno_discover_servers '{"server_names": ["akshare-stock-china"]}'
# 查看返回的工具列表，选择合适的工具调用
```

## 工作流建议

1. **不确定用哪个 server？** 对照上方目录，按功能类别找到目标 server
2. **不确定工具参数？** 先 `discover` 获取 inputSchema，再按 schema 填参数
3. **调用失败？** 检查 `mcpx status` 确认 token 有效；检查 server_names 拼写
4. **需要 OAuth 的 server？** discover 会返回 `auth_url`，用户需先授权

## 凭证管理

| 项目 | 路径 |
|------|------|
| Token 文件 | `~/.uno/tokens.json` |
| MCP 网关 | `https://uno.mcpmarket.cn/mcp` |
| 登录命令 | `mcpx login --headless` |
| 登出命令 | `mcpx logout` |

Token 有效期 30 天，过期后重新执行 `mcpx login --headless`。
