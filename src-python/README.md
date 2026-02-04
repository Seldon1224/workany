# WorkAny API - Python Implementation

Python/FastAPI 版本的 WorkAny API,使用 Claude Agent SDK 提供 AI Agent 功能。

## 要求

- Python 3.10+
- Claude Code CLI (通过 `pip install claude-agent-sdk` 自动安装)

## 安装

```bash
cd src-python

# 创建虚拟环境(推荐)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 配置

设置环境变量:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

或者在请求中提供 API 密钥。

## 运行

### 开发模式

```bash
# 方式 1: 使用 uvicorn
uvicorn app.main:app --reload --port 2026

# 方式 2: 直接运行
python -m app.main
```

### 生产模式

```bash
export PORT=2620
uvicorn app.main:app --host 0.0.0.0 --port 2620
```

## API 端点

服务器启动后访问 `http://localhost:2026`

### 核心端点

- `GET /` - API 信息
- `GET /health` - 健康检查
- `POST /agent/` - 执行 Agent (SSE 流式响应)
- `POST /agent/stop/{sessionId}` - 停止 Agent
- `GET /agent/session/{sessionId}` - 获取会话状态
- `POST /files/readdir` - 读取目录
- `POST /files/read` - 读取文件
- `POST /files/stat` - 获取文件状态
- `GET /files/skills-dir` - 获取技能目录
- `GET /mcp/config` - 读取 MCP 配置
- `POST /mcp/config` - 保存 MCP 配置

### API 文档

访问 `http://localhost:2026/docs` 查看自动生成的 API 文档(Swagger UI)。

## 项目结构

```
src-python/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── api/                 # API 路由
│   │   ├── health.py
│   │   ├── agent.py
│   │   ├── files.py
│   │   └── mcp.py
│   └── middleware/          # 中间件
│       └── cors.py
├── core/
│   └── agent/               # Agent 核心实现
│       ├── base.py
│       ├── claude.py
│       └── types.py
├── shared/
│   ├── services/            # 服务层
│   │   └── agent.py
│   ├── utils/               # 工具函数
│   │   ├── logger.py
│   │   └── paths.py
│   └── types/               # 类型定义
│       └── agent.py
├── config/                  # 配置
│   ├── constants.py
│   └── loader.py
├── requirements.txt         # 依赖
└── pyproject.toml          # 项目配置
```

## 与 TypeScript 版本的对比

### 已实现功能

- ✅ Health API
- ✅ Agent API (SSE 流式响应)
- ✅ Files API (目录读取、文件读取)
- ✅ MCP API (配置读写)
- ✅ CORS 中间件
- ✅ 日志系统

### 简化/待实现功能

- ⚠️ Sandbox API (计划简化,仅保留 Native 提供商)
- ⚠️ Preview API (依赖 Node.js,待实现)
- ⚠️ Providers API (待实现)

## 测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx

# 运行测试
pytest tests/ -v
```

## 开发

### 代码格式化

```bash
pip install black isort
black .
isort .
```

### 类型检查

```bash
pip install mypy
mypy .
```

## 注意事项

1. **Claude Code 依赖**: Python SDK 依赖 `claude-code` CLI,会在安装 SDK 时自动安装
2. **API 兼容性**: 保持与 TypeScript 版本的 API 接口完全兼容
3. **性能**: Python 异步性能可能与 Node.js 略有差异,但对于 AI Agent 应用影响不大

## 许可证

与主项目相同
