"""Image recognition tool for Claude Agent SDK."""
import base64
import os
from pathlib import Path
from typing import Any, Optional

import aiofiles
import httpx

from shared.provider.manager import get_provider_manager
from shared.utils.logger import create_logger

logger = create_logger("RecognizeImage")
from claude_agent_sdk import tool


# Supported image formats
SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@tool(
    "RecognizeImage",
    "Analyze and recognize content in an image file using Claude's vision capabilities",
    {
        "imagePath": str,  # Absolute path to the image file
        "question": str,   # Optional question about the image (default: "请详细描述这张图片的内容")
    }
)
async def recognize_image_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Recognize and analyze image content using Anthropic Vision API.
    
    Args:
        args: Dictionary containing:
            - imagePath: Absolute path to the image file
            - question: Optional question about the image
    
    Returns:
        Dictionary with content array containing the analysis result
    """
    image_path = args.get("imagePath")
    question = args.get("question", "请详细描述这张图片的内容")
    
    if not image_path:
        return {
            "content": [{
                "type": "text",
                "text": "Error: imagePath is required"
            }],
            "isError": True
        }
    
    try:
        # Expand ~ to home directory
        expanded_path = os.path.expanduser(image_path)
        file_path = Path(expanded_path)
        
        # Validate file exists
        if not file_path.exists():
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: Image file not found: {image_path}"
                }],
                "isError": True
            }
        
        # Validate file extension
        if file_path.suffix.lower() not in SUPPORTED_FORMATS:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: Unsupported image format. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
                }],
                "isError": True
            }
        
        # Validate file size
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: Image file too large ({file_size / 1024 / 1024:.2f}MB). Maximum size: 5MB"
                }],
                "isError": True
            }
        
        # Read image file
        async with aiofiles.open(file_path, "rb") as f:
            image_data = await f.read()
        
        # Determine media type
        media_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_type_map.get(file_path.suffix.lower(), "image/jpeg")
        
        # Encode image to base64
        import base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        # Get provider configuration
        provider_manager = get_provider_manager()
        provider_config = provider_manager.get_config()
        
        # Get API configuration from agent provider
        agent_config = provider_config.agent
        if not agent_config or not agent_config.config:
            # Fallback to environment variable
            api_key = os.getenv("ANTHROPIC_API_KEY")
            base_url = "https://api.anthropic.com/v1/messages"
            model = "claude-3-5-sonnet-20241022"
        else:
            api_key = agent_config.config.get("apiKey") or os.getenv("ANTHROPIC_API_KEY")
            base_url = agent_config.config.get("baseUrl", "https://api.anthropic.com/v1/messages")
            model = agent_config.config.get("model", "claude-3-5-sonnet-20241022")
            
            # Ensure base_url ends with /messages if it's just the base API URL
            if not base_url.endswith("/messages"):
                if base_url.endswith("/v1"):
                    base_url = f"{base_url}/messages"
                elif not base_url.endswith("/"):
                    base_url = f"{base_url}/v1/messages"
        
        if not api_key:
            return {
                "content": [{
                    "type": "text",
                    "text": "Error: API key not configured. Please configure provider settings."
                }],
                "isError": True
            }
        
        logger.info(f"[RecognizeImage] Using model: {model}, base_url: {base_url}")
        
        # Call Vision API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                base_url,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": image_base64,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": question,
                                },
                            ],
                        }
                    ],
                },
            )
        
        # 7. Parse response
        result = response.json()
        
        if "error" in result:
            return {
                "content": [
                    {"type": "text", "text": f"识别失败: {result['error'].get('message', '未知错误')}"}
                ],
                "isError": True,
            }
        
        # Extract text from response
        text = "无法识别图片内容"
        if "content" in result:
            for content_block in result["content"]:
                if content_block.get("type") == "text":
                    text = content_block.get("text", text)
                    break
        
        logger.info(f"[RecognizeImage] Recognition successful, result length: {len(text)}")
        
        return {
            "content": [{"type": "text", "text": text}],
        }
    
    except Exception as e:
        logger.error(f"[RecognizeImage] Error: {e}", exc_info=True)
        return {
            "content": [
                {"type": "text", "text": f"图片识别失败: {str(e)}"}
            ],
            "isError": True,
        }


def create_recognize_image_tool_spec(
    api_key: str,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> dict[str, Any]:
    """Create RecognizeImage tool specification for MCP server.
    
    Args:
        api_key: API key for the LLM provider
        base_url: Base URL for the API (optional)
        model: Model to use for recognition (optional)
    
    Returns:
        Tool specification dict
    """
    return {
        "name": "RecognizeImage",
        "description": """识别和分析图片内容。当需要查看、理解或分析图片文件时使用此工具。

支持的格式: PNG, JPG, JPEG, GIF, WEBP
最大文件大小: 5MB

使用场景:
- 识别验证码
- 分析截图内容
- 理解图表和数据可视化
- 提取图片中的文字
- 描述图片内容""",
        "input_schema": {
            "type": "object",
            "properties": {
                "imagePath": {
                    "type": "string",
                    "description": "图片文件的绝对路径,例如: /path/to/image.png",
                },
                "question": {
                    "type": "string",
                    "description": '关于图片的问题或需要分析的内容(可选)。例如: "请识别验证码", "请描述图片内容", "请提取图片中的文字"。默认为"请描述这张图片的内容"',
                },
            },
            "required": ["imagePath"],
        },
        "handler": lambda args: recognize_image(
            args["imagePath"],
            args.get("question"),
            api_key,
            base_url,
            model,
        ),
    }
