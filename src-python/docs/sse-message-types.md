# SSE 消息类型对比

## TypeScript 版本 vs Python 版本

### 消息类型完整列表

| 消息类型 | TypeScript | Python | 状态 |
|---------|-----------|--------|------|
| `session` | ✅ | ✅ | 已实现 |
| `text` | ✅ | ✅ | 已实现 |
| `tool_use` | ✅ | ✅ | 已实现 |
| `tool_result` | ✅ | ✅ | **刚刚添加** |
| `thinking` | ✅ | ✅ | 已实现 |
| `system` | ✅ | ✅ | 已实现 |
| `complete` | ✅ | ✅ | 已实现 |
| `error` | ✅ | ✅ | 已实现 |

---

## 消息格式详解

### 1. session
**发送时机**: Agent 开始执行时
```json
{
  "type": "session",
  "sessionId": "abc123"
}
```

### 2. text
**发送时机**: Agent 输出文本内容
```json
{
  "type": "text",
  "content": "这是 Agent 的回复..."
}
```

### 3. tool_use
**发送时机**: Agent 调用工具
```json
{
  "type": "tool_use",
  "tool": "Read",
  "toolUseId": "toolu_123",
  "input": {
    "file_path": "/path/to/file"
  }
}
```

### 4. tool_result ✨ 新增
**发送时机**: 工具执行完成,返回结果
```json
{
  "type": "tool_result",
  "toolUseId": "toolu_123",
  "output": "文件内容...",
  "isError": false
}
```
```

**重要性**:
- 前端可以显示工具执行的结果
- 用户可以看到每个工具调用的输出
- 帮助调试和理解 Agent 的执行过程

### 5. thinking
**发送时机**: Agent 的思考过程(如果启用)
```json
{
  "type": "thinking",
  "content": "我需要先读取文件..."
}
```

### 6. system
**发送时机**: 系统级消息
```json
{
  "type": "system",
  "subtype": "info",
  "data": {...}
}
```

### 7. complete
**发送时机**: Agent 执行完成
```json
{
  "type": "complete",
  "sessionId": "abc123",
  "durationMs": 5000,
  "numTurns": 3,
  "totalCostUsd": 0.05
}
```

### 8. error
**发送时机**: 发生错误
```json
{
  "type": "error",
  "message": "错误信息"
}
```

---

## 实现细节

### TypeScript 版本 (processMessage)

```typescript
// 处理 assistant 消息
if (msg.type === 'assistant' && msg.message?.content) {
  for (const block of msg.message.content) {
    if ('text' in block) {
      yield { type: 'text', content: block.text };
    } else if ('name' in block && 'id' in block) {
      yield { type: 'tool_use', id: block.id, name: block.name, input: block.input };
    }
  }
}

// 处理 user 消息 (tool_result)
if (msg.type === 'user' && msg.message?.content) {
  for (const block of msg.message.content) {
    if (block.type === 'tool_result') {
      yield {
        type: 'tool_result',
        toolUseId: block.tool_use_id,
        output: typeof block.content === 'string' ? block.content : JSON.stringify(block.content),
        isError: block.is_error || false,
      };
    }
  }
}
```

### Python 版本 (run 方法)

```python
# 处理 assistant 消息
if isinstance(msg, AssistantMessage):
    for block in msg.content:
        if isinstance(block, TextBlock):
            yield {"type": "text", "content": block.text}
        elif isinstance(block, ToolUseBlock):
            yield {"type": "tool_use", "tool": block.name, "toolUseId": block.id, "input": block.input}
        elif isinstance(block, ThinkingBlock):
            yield {"type": "thinking", "content": block.thinking}

# 处理 user 消息 (tool_result) ✨ 新增
elif isinstance(msg, UserMessage):
    for block in msg.content:
        if isinstance(block, ToolResultBlock):
            output = block.content
            if not isinstance(output, str):
                output = json.dumps(output)
            yield {
                "type": "tool_result",
                "toolUseId": block.tool_use_id,
                "output": output,
                "isError": block.is_error or False,
            }
```

---

## 前端使用示例

```typescript
const eventSource = new EventSource('/agent');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'session':
      console.log('Session started:', data.session_id);
      break;
    
    case 'text':
      appendMessage(data.content);
      break;
    
    case 'tool_use':
      showToolExecution(data.tool, data.input);
      break;
    
    case 'tool_result': // ✨ 现在可以处理了
      showToolResult(data.tool_use_id, data.output, data.is_error);
      break;
    
    case 'complete':
      showCompletion(data);
      break;
  }
};
```

---

## 修复内容

### 问题
Python 版本缺少 `tool_result` 消息,导致前端无法显示工具执行结果。

### 解决方案
1. ✅ 添加 `UserMessage` 导入
2. ✅ 在消息处理循环中添加 `UserMessage` 处理
3. ✅ 提取 `ToolResultBlock` 并发送 `tool_result` 消息
4. ✅ 处理输出格式(字符串或 JSON)
5. ✅ 包含 `is_error` 标志

### 影响
- 前端现在可以完整显示 Agent 的执行过程
- 用户可以看到每个工具的输入和输出
- 调试和理解 Agent 行为更容易

---

## 测试建议

### 1. 基础工具调用
```bash
# 请求: 读取文件 /path/to/file.txt
# 应该看到:
# - tool_use: Read
# - tool_result: 文件内容
```

### 2. 多个工具调用
```bash
# 请求: 搜索并读取文件
# 应该看到:
# - tool_use: Glob
# - tool_result: 文件列表
# - tool_use: Read
# - tool_result: 文件内容
```

### 3. 错误处理
```bash
# 请求: 读取不存在的文件
# 应该看到:
# - tool_use: Read
# - tool_result: 错误信息 (is_error: true)
```
