# 图片识别工具注册说明

## 问题

Python 版本虽然创建了 `RecognizeImage` 工具,但没有正确注册到 Claude Agent SDK 中。

## TypeScript 版本的实现

TypeScript 版本通过创建 `utility` MCP 服务器来注册工具:

```typescript
// 创建 utility MCP 服务器
function createUtilityMcpServer(apiKey: string, baseUrl?: string, model?: string) {
  return createSdkMcpServer({
    name: 'utility',
    version: '1.0.0',
    tools: [createRecognizeImageTool(apiKey, baseUrl, model)],
  });
}

// 在 run 方法中添加到 mcpServers
mcpServers.utility = createUtilityMcpServer(
  this.config.apiKey || '',
  this.config.baseUrl,
  this.config.model
);

queryOptions.mcpServers = mcpServers;
```

## Python SDK 的限制

Python `claude-agent-sdk` 可能不支持 `createSdkMcpServer` 这样的动态 MCP 服务器创建 API。

## 解决方案

### 方案 1: RecognizeImage 是内置工具(当前实现)

如果 `RecognizeImage` 是 Claude Code 的内置工具,只需要:
1. ✅ 添加到 `allowed_tools` 列表
2. ✅ 在 workspace instruction 中说明使用方法

**优点**: 简单,不需要额外配置
**缺点**: 依赖 Claude Code 内置支持

### 方案 2: 通过 MCP 配置文件注册

创建一个 MCP 配置文件来注册工具:

```json
// ~/.workany/mcp.json
{
  "mcpServers": {
    "utility": {
      "type": "stdio",
      "command": "python",
      "args": ["/path/to/utility_mcp_server.py"]
    }
  }
}
```

然后创建独立的 MCP 服务器脚本:

```python
# utility_mcp_server.py
from mcp import Server
from core.agent.tools.recognize_image import recognize_image

server = Server("utility")

@server.tool("RecognizeImage")
async def recognize_image_tool(imagePath: str, question: str = None):
    return await recognize_image(imagePath, question)

if __name__ == "__main__":
    server.run()
```

**优点**: 标准 MCP 协议,灵活
**缺点**: 需要额外的进程管理

### 方案 3: 使用 Python SDK 的自定义工具 API(如果支持)

如果 Python SDK 支持自定义工具注册:

```python
from claude_agent_sdk import tool

@tool("RecognizeImage", description="...")
async def recognize_image_tool(imagePath: str, question: str = None):
    return await recognize_image(imagePath, question)

sdk_options.custom_tools = [recognize_image_tool]
```

**优点**: 直接集成,无需外部进程
**缺点**: 需要 SDK 支持

## 当前状态

✅ **已实现**: 
- `RecognizeImage` 添加到 `allowed_tools`
- Workspace instruction 中包含使用说明
- 工具实现完整(`core/agent/tools/recognize_image.py`)

⚠️ **待确认**:
- Python SDK 是否内置支持 `RecognizeImage`
- 是否需要额外的 MCP 服务器注册

## 测试方法

1. 启动 Python API
2. 发送请求让 Agent 识别图片
3. 查看日志,确认工具是否被调用

如果工具无法使用,考虑实现方案 2(MCP 配置文件)。
