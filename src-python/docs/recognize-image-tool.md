# Python 版本图片识别工具实现

## 概述

已为 Python 版本实现了 `RecognizeImage` 工具,功能与 TypeScript 版本完全一致。

## 实现位置

- **工具实现**: `core/agent/tools/recognize_image.py`
- **集成位置**: `core/agent/claude.py` (已添加到 `allowed_tools`)

## 功能特性

### 支持的格式
- PNG
- JPG/JPEG
- GIF
- WEBP

### 限制
- 最大文件大小: 5MB
- 需要配置 API Key (ANTHROPIC_API_KEY)

### 使用场景
- 识别验证码
- 分析截图内容
- 理解图表和数据可视化
- 提取图片中的文字
- 描述图片内容

## API 参数

```python
async def recognize_image(
    image_path: str,           # 图片文件的绝对路径
    question: Optional[str],   # 关于图片的问题(可选)
    api_key: Optional[str],    # API key
    base_url: Optional[str],   # API base URL
    model: Optional[str],      # 模型名称
) -> dict[str, Any]
```

## 工具规范

```json
{
  "name": "RecognizeImage",
  "input_schema": {
    "type": "object",
    "properties": {
      "imagePath": {
        "type": "string",
        "description": "图片文件的绝对路径"
      },
      "question": {
        "type": "string",
        "description": "关于图片的问题(可选)"
      }
    },
    "required": ["imagePath"]
  }
}
```

## 实现细节

### 1. 文件验证
- 检查文件是否存在
- 验证文件大小(≤5MB)
- 验证文件格式(支持的扩展名)

### 2. 图片处理
- 异步读取图片文件
- Base64 编码
- 确定正确的 MIME 类型

### 3. API 调用
- 使用 Anthropic Messages API
- 支持自定义 base URL (如 OpenRouter)
- 支持自定义模型
- 默认模型: `claude-sonnet-4-20250514`
- 最大 tokens: 2048
- 超时: 60 秒

### 4. 错误处理
- 文件不存在
- 文件过大
- 格式不支持
- API 调用失败
- 解析错误

## 与 TypeScript 版本的对比

| 功能 | TypeScript | Python | 状态 |
|------|-----------|--------|------|
| 基础图片识别 | ✅ | ✅ | 完全一致 |
| 支持的格式 | PNG, JPG, GIF, WEBP | PNG, JPG, GIF, WEBP | 完全一致 |
| 文件大小限制 | 5MB | 5MB | 完全一致 |
| API 调用 | fetch | httpx | 实现方式不同,功能一致 |
| 错误处理 | ✅ | ✅ | 完全一致 |
| 日志记录 | console.log | logger | 实现方式不同,功能一致 |
| 异步处理 | async/await | async/await | 完全一致 |

## 使用示例

### 在 Agent 中使用

Agent 会自动识别 `RecognizeImage` 工具,用户可以直接请求:

```
用户: 请帮我识别这张图片 /path/to/image.png 中的验证码
```

Agent 会自动调用 `RecognizeImage` 工具进行识别。

### 默认问题

如果用户没有指定问题,工具会使用默认问题:
```
"请描述这张图片的内容"
```

## 配置要求

### 环境变量
```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

### 或在代码中配置
```python
agent_config = AgentConfig(
    api_key="your_api_key",
    base_url="https://api.anthropic.com",  # 可选
    model="claude-sonnet-4-20250514",      # 可选
)
```

## 依赖项

已在 `requirements.txt` 中包含:
- `httpx` - HTTP 客户端
- `aiofiles` - 异步文件操作

## 测试建议

1. **基础功能测试**
   ```python
   result = await recognize_image(
       "/path/to/test.png",
       "请描述这张图片"
   )
   ```

2. **错误处理测试**
   - 不存在的文件
   - 过大的文件
   - 不支持的格式

3. **API 集成测试**
   - 验证 API 调用
   - 检查响应解析
   - 测试超时处理

## 注意事项

1. **API Key**: 必须配置有效的 Anthropic API Key
2. **网络**: 需要能够访问 Anthropic API
3. **文件路径**: 必须使用绝对路径
4. **异步**: 所有操作都是异步的,需要在 async 上下文中调用

## 后续优化

可能的改进方向:
- [ ] 支持批量图片识别
- [ ] 添加图片缓存机制
- [ ] 支持更多图片格式
- [ ] 添加图片预处理(压缩、裁剪等)
- [ ] 支持本地模型识别(离线模式)
