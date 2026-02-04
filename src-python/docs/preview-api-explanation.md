# Preview API 功能说明

## 概述

Preview API 用于管理 **Vite 开发服务器**,为用户提供 Web 应用的**实时预览**功能(Live Preview with HMR)。

## 核心功能

### 1. `/preview/status/:taskId` - 获取预览服务器状态

**作用**: 查询指定任务的 Vite 服务器运行状态

**请求**:
```http
GET /preview/status/1770194239634
```

**响应**:
```json
{
  "id": "preview-1770194239634",
  "taskId": "1770194239634",
  "status": "running",  // starting | running | stopped | error
  "url": "http://localhost:5173",
  "hostPort": 5173,
  "startedAt": "2026-02-04T08:30:00Z",
  "lastAccessedAt": "2026-02-04T08:35:00Z"
}
```

**状态说明**:
- `starting`: 服务器正在启动(安装依赖、启动 Vite)
- `running`: 服务器正在运行,可以访问
- `stopped`: 服务器已停止
- `error`: 服务器启动失败或运行错误

---

## 完整 API 列表

### 1. 检查 Node.js 可用性
```http
GET /preview/node-available
```
**响应**: `{ "available": true/false }`

**说明**: Live Preview 需要系统安装 Node.js,此接口检查是否可用

---

### 2. 启动预览服务器
```http
POST /preview/start
Content-Type: application/json

{
  "taskId": "1770194239634",
  "workDir": "~/.workany/sessions/task-xxx",
  "port": 5173  // 可选,默认自动分配
}
```

**功能**:
1. 检查是否已有运行中的服务器
2. 分配端口(5173-5273 范围)
3. 确保项目文件存在(package.json, vite.config.js, index.html)
4. 安装依赖(`npm install`)
5. 启动 Vite 开发服务器
6. 等待服务器就绪(最多 2 分钟)
7. 启动健康检查和空闲超时

---

### 3. 停止预览服务器
```http
POST /preview/stop
Content-Type: application/json

{
  "taskId": "1770194239634"
}
```

**功能**: 停止指定任务的 Vite 服务器,释放端口

---

### 4. 获取服务器状态
```http
GET /preview/status/:taskId
```

**功能**: 
- 查询服务器状态
- 更新最后访问时间
- 重置空闲超时

---

### 5. 停止所有服务器
```http
POST /preview/stop-all
```

**功能**: 停止所有正在运行的预览服务器

---

## 工作流程

### 典型使用场景

1. **Agent 创建 Web 应用**
   ```
   Agent 在 ~/.workany/sessions/task-xxx/ 创建 HTML/CSS/JS 文件
   ```

2. **前端请求启动预览**
   ```http
   POST /preview/start
   {
     "taskId": "task-xxx",
     "workDir": "~/.workany/sessions/task-xxx"
   }
   ```

3. **后端启动 Vite 服务器**
   ```
   - 创建 package.json (如果不存在)
   - 创建 vite.config.js (配置端口)
   - 运行 npm install
   - 启动 Vite
   - 等待服务器就绪
   ```

4. **前端轮询状态**
   ```http
   GET /preview/status/task-xxx
   
   响应: { "status": "starting" }  // 安装中
   响应: { "status": "running", "url": "http://localhost:5173" }  // 就绪
   ```

5. **用户访问预览**
   ```
   在浏览器中打开 http://localhost:5173
   享受 HMR 实时更新
   ```

6. **自动清理**
   ```
   - 30 分钟无访问 → 自动停止
   - 健康检查失败 → 自动停止
   - 最多 5 个并发预览
   ```

---

## 技术细节

### 端口管理
- **端口范围**: 5173-5273
- **分配策略**: 优先使用指定端口,否则自动分配
- **最大并发**: 5 个预览服务器

### 超时和清理
- **启动超时**: 120 秒(npm install + Vite 启动)
- **空闲超时**: 30 分钟无访问自动停止
- **健康检查**: 每 10 秒检查一次服务器状态

### 零配置支持
如果项目没有配置文件,自动创建:

**package.json**:
```json
{
  "name": "preview",
  "type": "module",
  "scripts": {
    "dev": "vite"
  },
  "devDependencies": {
    "vite": "~5.4.0"
  }
}
```

**vite.config.js**:
```js
export default {
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    watch: {
      usePolling: true,
    },
  },
  appType: 'mpa',
}
```

---

## Python 版本实现状态

### ❌ 未实现

Python 版本目前**没有实现** Preview API,原因:

1. **依赖 Node.js**: Preview 功能需要系统安装 Node.js/npm
2. **进程管理复杂**: 需要管理 Vite 子进程、健康检查、超时等
3. **优先级较低**: 核心 Agent 功能更重要

### 实现建议

如果需要实现,可以参考以下方案:

#### 方案 1: 完整实现(推荐)
```python
# shared/services/preview.py
class PreviewManager:
    async def start_preview(self, config: PreviewConfig) -> PreviewStatus:
        # 1. 检查 Node.js
        # 2. 分配端口
        # 3. 创建配置文件
        # 4. 运行 npm install
        # 5. 启动 Vite 进程
        # 6. 等待就绪
        # 7. 启动健康检查
        pass
```

#### 方案 2: 简化实现
```python
# 只提供状态查询,不管理 Vite 进程
# 假设用户手动启动 Vite
async def get_status(task_id: str) -> PreviewStatus:
    # 检查端口是否可访问
    # 返回简单状态
    pass
```

#### 方案 3: 返回 404(当前)
```python
# 前端会看到 404,知道功能未实现
# 可以显示提示信息
```

---

## 前端集成

### 检查功能可用性
```typescript
const response = await fetch('/preview/node-available');
const { available } = await response.json();

if (!available) {
  showMessage('Live Preview requires Node.js to be installed');
}
```

### 启动预览
```typescript
const response = await fetch('/preview/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    taskId: '1770194239634',
    workDir: '~/.workany/sessions/task-xxx'
  })
});

const status = await response.json();
if (status.status === 'starting') {
  // 开始轮询状态
  pollPreviewStatus(taskId);
}
```

### 轮询状态
```typescript
async function pollPreviewStatus(taskId: string) {
  const interval = setInterval(async () => {
    const response = await fetch(`/preview/status/${taskId}`);
    const status = await response.json();
    
    if (status.status === 'running') {
      clearInterval(interval);
      window.open(status.url, '_blank');
    } else if (status.status === 'error') {
      clearInterval(interval);
      showError(status.error);
    }
  }, 2000);  // 每 2 秒检查一次
}
```

---

## 总结

### Preview API 的作用
1. **实时预览**: 为 Web 应用提供 HMR 支持的实时预览
2. **自动化**: 自动安装依赖、配置 Vite、管理端口
3. **资源管理**: 自动清理空闲服务器,限制并发数量

### 为什么前端会调用这个 API
- 用户创建了 Web 应用(HTML/CSS/JS)
- 想要在浏览器中实时预览
- 前端需要知道预览服务器的状态和 URL

### Python 版本的现状
- ❌ 未实现
- 前端会收到 404 错误
- 可以考虑实现或提供替代方案(静态文件服务)
