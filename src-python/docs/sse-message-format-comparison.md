# SSE 消息格式对比 - TypeScript vs Python

## 完整对比表

| 消息类型 | TypeScript 字段 | Python 字段 | 状态 |
|---------|----------------|-------------|------|
| **session** | | | |
| - 类型 | `type: "session"` | `type: "session"` | ✅ |
| - 会话ID | `sessionId` | `sessionId` | ✅ |
| **text** | | | |
| - 类型 | `type: "text"` | `type: "text"` | ✅ |
| - 内容 | `content` | `content` | ✅ |
| **tool_use** | | | |
| - 类型 | `type: "tool_use"` | `type: "tool_use"` | ✅ |
| - 工具ID | `id` | `id` | ✅ |
| - 工具名称 | `name` | `name` | ✅ |
| - 输入参数 | `input` | `input` | ✅ |
| **tool_result** | | | |
| - 类型 | `type: "tool_result"` | `type: "tool_result"` | ✅ |
| - 工具ID | `toolUseId` | `toolUseId` | ✅ |
| - 输出 | `output` | `output` | ✅ |
| - 错误标志 | `isError` | `isError` | ✅ |
| **thinking** | | | |
| - 类型 | `type: "thinking"` | `type: "thinking"` | ✅ |
| - 内容 | `content` | `content` | ✅ |
| **system** | | | |
| - 类型 | `type: "system"` | `type: "system"` | ✅ |
| - 子类型 | `subtype` | `subtype` | ✅ |
| - 数据 | `data` | `data` | ✅ |
| **complete** | | | |
| - 类型 | `type: "complete"` | `type: "complete"` | ✅ |
| - 会话ID | `sessionId` | `sessionId` | ✅ |
| - 持续时间 | `durationMs` | `durationMs` | ✅ |
| - 轮次 | `numTurns` | `numTurns` | ✅ |
| - 成本 | `totalCostUsd` | `totalCostUsd` | ✅ |
| **error** | | | |
| - 类型 | `type: "error"` | `type: "error"` | ✅ |
| - 消息 | `message` | `message` | ✅ |

---

## 详细消息格式

### 1. session
```json
{
  "type": "session",
  "sessionId": "abc123"
}
```

### 2. text
```json
{
  "type": "text",
  "content": "Agent 的回复内容"
}
```

### 3. tool_use
```json
{
  "type": "tool_use",
  "id": "toolu_123",
  "name": "Read",
  "input": {
    "file_path": "/path/to/file"
  }
}
```

### 4. tool_result
```json
{
  "type": "tool_result",
  "toolUseId": "toolu_123",
  "output": "文件内容或工具执行结果",
  "isError": false
}
```

### 5. thinking
```json
{
  "type": "thinking",
  "content": "Agent 的思考过程"
}
```

### 6. system
```json
{
  "type": "system",
  "subtype": "info",
  "data": {...}
}
```

### 7. complete
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
```json
{
  "type": "error",
  "message": "错误信息"
}
```

---

## 关键差异说明

### tool_use vs tool_result

注意 `tool_use` 和 `tool_result` 使用不同的字段名来标识工具:

- **tool_use**: 使用 `id` 字段
  - 这是工具调用时生成的唯一标识符
  
- **tool_result**: 使用 `toolUseId` 字段
  - 这是对应的工具调用 ID,用于关联结果和调用

**为什么不同?**
- `tool_use` 是 Agent 发起的动作,`id` 是该动作的标识
- `tool_result` 是对某个动作的响应,`toolUseId` 引用原始动作

---

## 前端使用示例

```typescript
const toolCalls = new Map<string, ToolCall>();

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'tool_use':
      // 记录工具调用
      toolCalls.set(data.id, {
        name: data.name,
        input: data.input,
        status: 'pending'
      });
      showToolExecution(data.id, data.name, data.input);
      break;
    
    case 'tool_result':
      // 更新对应的工具调用结果
      const toolCall = toolCalls.get(data.toolUseId);
      if (toolCall) {
        toolCall.output = data.output;
        toolCall.status = data.isError ? 'error' : 'success';
        showToolResult(data.toolUseId, data.output, data.isError);
      }
      break;
  }
};
```

---

## 完整性检查 ✅

所有消息类型的字段命名现在与 TypeScript 版本**完全一致**:

- ✅ 使用 camelCase 命名规范
- ✅ `tool_use` 使用 `id` 和 `name`
- ✅ `tool_result` 使用 `toolUseId` 和 `isError`
- ✅ `complete` 使用 `sessionId`, `durationMs`, `numTurns`, `totalCostUsd`
- ✅ 所有其他消息类型字段一致
