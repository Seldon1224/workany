"""Image recognition tool for Claude Agent SDK."""
import base64
import os
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
import httpx

from shared.utils.logger import create_logger
from claude_agent_sdk import tool

logger = create_logger("RecognizeImage")


# Supported image formats
SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def create_recognize_image_tool(
    api_key: str,
    base_url: Optional[str] = None,
    model: Optional[str] = None
):
    """Create RecognizeImage tool with given API configuration.
    
    Args:
        api_key: Anthropic API key
        base_url: Optional base URL for API
        model: Optional model name
    
    Returns:
        RecognizeImage tool instance
    """
    
    @tool(
        "RecognizeImage",
        """识别和分析图片内容。当需要查看、理解或分析图片文件时使用此工具。

支持的格式: PNG, JPG, JPEG, GIF, WEBP
最大文件大小: 5MB

使用场景:
- 识别验证码
- 分析截图内容
- 理解图表和数据可视化
- 提取图片中的文字
- 描述图片内容""",
        {
            "imagePath": str,  # 图片文件的绝对路径，例如: /path/to/image.png
            "question": str,   # 关于图片的问题或需要分析的内容(可选)
        }
    )
    async def recognize_image_impl(args: Dict[str, Any]) -> Dict[str, Any]:
        """Recognize and analyze image content.
        
        Args:
            args: Tool arguments containing imagePath and optional question
        
        Returns:
            Tool result
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
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            
            # Use provided API configuration
            api_base_url = base_url or "https://api.anthropic.com"
            api_model = model or "claude-sonnet-4-20250514"
            
            # Ensure base_url ends with /v1/messages
            if not api_base_url.endswith("/messages"):
                if api_base_url.endswith("/v1"):
                    api_base_url = f"{api_base_url}/messages"
                elif not api_base_url.endswith("/"):
                    api_base_url = f"{api_base_url}/v1/messages"
            
            logger.info(f"[RecognizeImage] Using model: {api_model}, base_url: {api_base_url}")
            
            # Call Vision API
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    api_base_url,
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": api_model,
                        "max_tokens": 2048,
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
            
            if not response.is_success:
                error_text = response.text
                logger.error(f"[RecognizeImage] API error: {response.status_code} - {error_text}")
                return {
                    "content": [{
                        "type": "text",
                        "text": f"识别失败: {error_text}"
                    }],
                    "isError": True
                }
            
            # Parse response
            result = response.json()
            
            if "error" in result:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"识别失败: {result['error'].get('message', 'Unknown error')}"
                    }],
                    "isError": True
                }
            
            # Extract text from response
            text = "无法识别图片内容"
            if "content" in result and result["content"]:
                for content_block in result["content"]:
                    if content_block.get("type") == "text":
                        text = content_block.get("text", text)
                        break
            
            logger.info(f"[RecognizeImage] Recognition successful, result length: {len(text)}")
            
            return {
                "content": [{
                    "type": "text",
                    "text": text
                }]
            }
            
        except Exception as e:
            logger.error(f"[RecognizeImage] Error: {e}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"图片识别失败: {str(e)}"
                }],
                "isError": True
            }
    
    return recognize_image_impl
