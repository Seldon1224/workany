# Claude Agent 配置对比

## 已实现的配置项 ✅

### 基础配置
- ✅ `cwd` - 工作目录
- ✅ `model` - 模型选择
- ✅ `env` - 环境变量配置(API key, base URL)

### 工具配置
- ✅ `tools` - 工具预设 (`{"type": "preset", "preset": "claude_code"}`)
- ✅ `allowed_tools` - 允许的工具列表
  - Read, Edit, Write, Glob, Grep, Bash
  - WebSearch, WebFetch, Skill, Task, LSP, TodoWrite

### Skills 配置
- ✅ `setting_sources` - 设置源 (`["user", "project"]`)
  - `user`: 从 `~/.claude/skills/` 加载
  - `project`: 从项目 `.claude/skills/` 加载
  - 支持通过 `skillsConfig.enabled` 控制

### 权限配置
- ✅ `permission_mode` - 权限模式 (`"bypassPermissions"`)
- ✅ `allow_dangerously_skip_permissions` - 跳过权限检查 (`True`)

### 执行配置
- ✅ `max_turns` - 最大轮次 (200)

---

## 待实现的功能 ⚠️

### 1. MCP 服务器配置
TypeScript 版本在第 1206-1268 行实现了完整的 MCP 服务器加载:

```typescript
// Load user-configured MCP servers
const userMcpServers = await loadMcpServers(options?.mcpConfig);

// Initialize MCP servers
const mcpServers = {
  ...userMcpServers,
};

// Add sandbox MCP server if enabled
if (options?.sandbox?.enabled) {
  mcpServers.sandbox = createSandboxMcpServer(options.sandbox.provider);
}

// Add utility MCP server (for image recognition)
mcpServers.utility = createUtilityMcpServer(apiKey, baseUrl, model);

// Add to query options
queryOptions.mcpServers = mcpServers;
```

**Python 需要实现**:
- ❌ `loadMcpServers()` - 从配置文件加载 MCP 服务器
- ❌ `createSandboxMcpServer()` - 创建 Sandbox MCP 服务器
- ❌ `createUtilityMcpServer()` - 创建工具 MCP 服务器
- ❌ `sdk_options.mcp_servers` - 配置 MCP 服务器

### 2. Sandbox 集成
TypeScript 版本支持 Sandbox 模式:

```typescript
if (options?.sandbox?.enabled) {
  mcpServers.sandbox = createSandboxMcpServer(options.sandbox.provider);
  queryOptions.allowedTools = [
    ...ALLOWED_TOOLS,
    'sandbox_run_script',
    'sandbox_run_command',
  ];
}
```

**Python 需要实现**:
- ❌ Sandbox MCP 服务器
- ❌ `sandbox_run_script` 工具
- ❌ `sandbox_run_command` 工具

### 3. 图片处理
TypeScript 版本支持图片附件:

```typescript
if (options?.images && options.images.length > 0) {
  const imagePaths = await saveImagesToDisk(options.images, sessionCwd);
  imageInstruction = `...MANDATORY IMAGE ANALYSIS...`;
}
```

**Python 需要实现**:
- ❌ `saveImagesToDisk()` - 保存图片到磁盘
- ❌ 图片分析指令注入
- ❌ `RecognizeImage` 工具

### 4. Claude Code 路径
TypeScript 版本确保 Claude Code 已安装:

```typescript
const claudeCodePath = await ensureClaudeCode();
queryOptions.pathToClaudeCodeExecutable = claudeCodePath;
```

**Python 需要实现**:
- ❌ `ensureClaudeCode()` - 确保 Claude Code 已安装
- ❌ `sdk_options.path_to_claude_code_executable` - 配置路径

### 5. 会话管理
TypeScript 版本有完整的会话管理:

```typescript
const session = this.createSession('executing');
yield { type: 'session', sessionId: session.id };
```

**Python 需要实现**:
- ❌ 会话创建和管理
- ❌ 发送 session 消息

### 6. 工作区指令
TypeScript 版本添加工作区指令到 prompt:

```typescript
const enhancedPrompt = 
  getWorkspaceInstruction(sessionCwd, sandboxOpts) +
  conversationContext +
  prompt;
```

**Python 需要实现**:
- ❌ `getWorkspaceInstruction()` - 生成工作区指令
- ❌ Sandbox 选项传递

---

## Python SDK API 限制

根据搜索结果,Python Claude Agent SDK 的 API 与 TypeScript 版本有所不同:

### Python SDK 支持的选项
- ✅ `model` - 模型选择
- ✅ `cwd` - 工作目录
- ✅ `allowed_tools` - 允许的工具
- ✅ `permission_mode` - 权限模式
- ✅ `setting_sources` - 设置源
- ✅ `mcp_servers` - MCP 服务器
- ✅ `max_turns` - 最大轮次
- ⚠️ `yolo` - 自动确认模式(TypeScript 用 `bypassPermissions`)
- ⚠️ `timeout` - 超时设置
- ⚠️ `system_prompt` - 系统提示

### Python SDK 可能不支持的选项
- ❓ `pathToClaudeCodeExecutable` - 可能不需要(Python SDK 自动管理)
- ❓ `tools.preset` - 需要确认格式
- ❓ `allowDangerouslySkipPermissions` - 可能用 `yolo` 替代

---

## 下一步行动

### 优先级 1 - 核心功能
1. ✅ 添加基础配置项(已完成)
2. ⚠️ 实现 MCP 服务器加载
3. ⚠️ 添加会话管理
4. ⚠️ 添加工作区指令

### 优先级 2 - 扩展功能
5. ⚠️ 实现 Sandbox 集成
6. ⚠️ 实现图片处理
7. ⚠️ 确保 Claude Code 安装

### 优先级 3 - 优化
8. ⚠️ 错误处理优化
9. ⚠️ 日志记录完善
10. ⚠️ 性能优化

---

## 当前状态

✅ **基础配置已完成** - 核心的 SDK 选项已经配置
⚠️ **MCP 和 Sandbox 待实现** - 需要额外的服务层支持
⚠️ **图片处理待实现** - 需要文件操作和工具集成

**建议**: 先完成 MCP 服务器加载和会话管理,这些是核心功能。Sandbox 和图片处理可以作为后续增强。
