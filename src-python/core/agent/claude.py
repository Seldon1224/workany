"""Claude Agent SDK implementation."""
import asyncio
import hashlib
import os
from pathlib import Path
from typing import AsyncGenerator, Optional

import aiofiles

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk import (
    AssistantMessage,
    UserMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ThinkingBlock,
    ResultMessage,
    SystemMessage,
)

from core.agent.base import IAgent
from core.agent.types import (
    AgentConfig,
    AgentMessage,
    AgentOptions,
    AgentProvider,
    ConversationMessage,
)
from config.constants import DEFAULT_WORK_DIR
from shared.utils.logger import create_logger

logger = create_logger("ClaudeAgent")

# Default allowed tools
ALLOWED_TOOLS = [
    "read_file",
    "write_file",
    "list_directory",
    "search_files",
    "execute_command",
    "browser",
]


class ClaudeAgent(IAgent):
    """Claude Agent SDK implementation."""
    
    @property
    def provider(self) -> AgentProvider:
        """Get the provider type."""
        return AgentProvider.CLAUDE
    
    @property
    def name(self) -> str:
        """Get the human-readable name."""
        return "Claude Agent"
    
    async def is_available(self) -> bool:
        """Check if Claude Agent is available.
        
        Returns:
            True if available (API key is set)
        """
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        return api_key is not None
    
    def _build_env_config(self) -> dict[str, str]:
        """Build environment variables for the SDK.
        
        Returns:
            Environment variables dict
        """
        env = {}
        
        # API Key
        if self.config.api_key:
            env["ANTHROPIC_API_KEY"] = self.config.api_key
        
        # Base URL (for custom endpoints like OpenRouter)
        if self.config.base_url:
            env["ANTHROPIC_BASE_URL"] = self.config.base_url
        
        return env
    
    async def _save_images_to_disk(
        self,
        images: list,
        work_dir: str
    ) -> list[str]:
        """Save image attachments to disk.
        
        Args:
            images: List of ImageAttachment objects
            work_dir: Working directory to save images
        
        Returns:
            List of saved image file paths
        """
        import base64
        import time
        
        saved_paths = []
        
        if not images:
            return saved_paths
        
        # Ensure work directory exists
        Path(work_dir).mkdir(parents=True, exist_ok=True)
        
        for i, image in enumerate(images):
            try:
                # Determine file extension from MIME type
                ext = image.mime_type.split('/')[-1] if image.mime_type else 'png'
                filename = f"image_{int(time.time() * 1000)}_{i}.{ext}"
                file_path = Path(work_dir) / filename
                
                # Remove data URL prefix if present (e.g., "data:image/png;base64,")
                base64_data = image.data
                if ',' in base64_data:
                    base64_data = base64_data.split(',', 1)[1]
                
                # Decode and save
                image_bytes = base64.b64decode(base64_data)
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(image_bytes)
                
                saved_paths.append(str(file_path))
                logger.info(f"Saved image to: {file_path}")
            except Exception as e:
                logger.error(f"Failed to save image {i}: {e}")
        
        return saved_paths
    
    def _format_conversation_history(
        self,
        conversation: Optional[list[ConversationMessage]]
    ) -> str:
        """Format conversation history for inclusion in prompt.
        
        Args:
            conversation: List of conversation messages
        
        Returns:
            Formatted conversation history string
        """
        if not conversation:
            return ""
        
        history_lines = ["<conversation_history>"]
        for msg in conversation:
            role = msg.role.upper()
            content = msg.content
            history_lines.append(f"\n{role}: {content}")
        history_lines.append("\n</conversation_history>\n")
        
        return "\n".join(history_lines)
    
    async def run(
        self,
        prompt: str,
        options: Optional[AgentOptions] = None
    ) -> AsyncGenerator[AgentMessage, None]:
        """Run the Claude Agent.
        
        Args:
            prompt: User prompt
            options: Optional execution options
        
        Yields:
            Agent messages (SSE events)
        """
        options = options or AgentOptions()
        
        # Build full prompt with workspace instruction and conversation history
        from core.agent.workspace import get_workspace_instruction
        
        # Build SDK options
        sdk_options = ClaudeAgentOptions()
        
        # Set working directory and expand ~ to home directory
        cwd = options.cwd or DEFAULT_WORK_DIR
        if cwd.startswith("~"):
            cwd = os.path.expanduser(cwd)
        Path(cwd).mkdir(parents=True, exist_ok=True)
        
        # Handle image attachments - save to disk and reference in prompt
        image_instruction = ""
        if options.images and len(options.images) > 0:
            logger.info(f"Processing {len(options.images)} image(s)")
            for i, img in enumerate(options.images):
                logger.info(f"Image {i}: mimeType={img.mime_type}, dataLength={len(img.data)}")
            
            saved_image_paths = await self._save_images_to_disk(options.images, cwd)
            logger.info(f"Saved {len(saved_image_paths)} images to disk: {', '.join(saved_image_paths)}")
            
            if saved_image_paths:
                images_list = '\n'.join([f"{i+1}. {p}" for i, p in enumerate(saved_image_paths)])
                image_instruction = f"""
## 🖼️ MANDATORY IMAGE ANALYSIS - DO THIS FIRST

**STOP! Before doing anything else, you MUST read the attached image(s).**

The user has attached {len(saved_image_paths)} image file(s):
{images_list}

**YOUR FIRST ACTION MUST BE:**
Use the Read tool to view each image file listed above. The Read tool supports image files (PNG, JPG, etc.) and will show you the visual content.

Example:
```
Read tool: file_path="{saved_image_paths[0]}"
```

**CRITICAL RULES:**
- DO NOT respond to the user's question until you have READ and SEEN the actual image content
- DO NOT guess or assume what the image contains
- After reading the image, describe what you actually see in the image
- Base your response ONLY on the actual visual content you observe

---
User's request (answer this AFTER reading the images):
"""
        
        # Get workspace instruction
        workspace_instruction = get_workspace_instruction(cwd, options.sandbox)
        
        # Build conversation history
        conversation_context = ""
        if options.conversation:
            history = self._format_conversation_history(options.conversation)
            conversation_context = history + "\n"
        
        # Combine: workspace instruction + conversation + image instruction (if any) + prompt
        full_prompt = workspace_instruction + conversation_context
        if image_instruction:
            full_prompt += image_instruction
        full_prompt += prompt

        
        # Build environment config
        env_config = self._build_env_config()
        
        # Set environment variables before creating client
        for key, value in env_config.items():
            if value is not None:
                os.environ[key] = value
        
        # Configure tools preset
        sdk_options.tools = {"type": "preset", "preset": "claude_code"}
        
        # Configure allowed tools
        allowed_tools = list(options.allowed_tools or ALLOWED_TOOLS)
        
        # Add RecognizeImage tool (from utility MCP server)
        # Tool name format: mcp__{server_name}__{tool_name}
        if "mcp__utility__RecognizeImage" not in allowed_tools:
            allowed_tools.append("mcp__utility__RecognizeImage")
        
        # Add sandbox tools if enabled
        if options.sandbox and options.sandbox.enabled:
            sandbox_tools = [
                "sandbox_run_script",
                "sandbox_run_command",
                "sandbox_list_files",
                "sandbox_read_file",
                "sandbox_write_file",
            ]
            for tool in sandbox_tools:
                if tool not in allowed_tools:
                    allowed_tools.append(tool)
        
        sdk_options.allowed_tools = allowed_tools
        logger.info(f"Allowed tools: {len(allowed_tools)} tools")
        
        # Configure setting sources for skills
        # - 'user' loads from ~/.claude/skills/
        # - 'project' loads from project/.claude/skills/
        setting_sources = ["user", "project"]
        if options.skills_config and not options.skills_config.enabled:
            setting_sources = ["project"]  # Disable user skills
        sdk_options.setting_sources = setting_sources
        
        # Configure permission mode
        sdk_options.permission_mode = "bypassPermissions"
        sdk_options.allow_dangerously_skip_permissions = True
        
        # Configure model if specified
        if self.config.model:
            sdk_options.model = self.config.model
        
        # Configure max turns (allow more agentic iterations)
        sdk_options.max_turns = 200
        
        # Configure working directory
        sdk_options.cwd = cwd
        
        # Load and configure MCP servers
        from shared.mcp.loader import load_mcp_servers
        from claude_agent_sdk import create_sdk_mcp_server
        
        mcp_config_dict = None
        if options.mcp_config:
            mcp_config_dict = {"enabled": options.mcp_config.enabled}
        
        user_mcp_servers = await load_mcp_servers(mcp_config_dict)
        
        # Create utility MCP server for image recognition
        # Pass API key from config to the tool factory function
        from core.agent.tools.recognize_image import create_recognize_image_tool
        
        utility_server = create_sdk_mcp_server(
            name="utility",
            version="1.0.0",
            tools=[create_recognize_image_tool(
                api_key=self.config.api_key or "",
                base_url=self.config.base_url,
                model=self.config.model
            )]
        )
        
        # Combine user MCP servers with utility server
        all_mcp_servers = {**(user_mcp_servers or {}), "utility": utility_server}
        
        # Add MCP servers to SDK options
        sdk_options.mcp_servers = all_mcp_servers
        logger.info(f"MCP servers loaded: {', '.join(all_mcp_servers.keys())}")
        
        # Track sent messages to avoid duplicates
        sent_text_hashes: set[str] = set()
        sent_tool_ids: set[str] = set()
        
        # Generate session ID for tracking
        from nanoid import generate
        session_id = generate()
        
        logger.info(f"Starting Claude Agent session {session_id}")
        logger.info(f"Prompt: {prompt[:100]}...")
        logger.info(f"Working directory: {cwd}")
        logger.info(f"Setting sources: {setting_sources}")
        logger.info(f"Allowed tools: {len(allowed_tools)} tools")
        
        # Send session ID to client
        yield {
            "type": "session",
            "sessionId": session_id,
        }
        
        try:
            # Create SDK client with configured options
            async with ClaudeSDKClient(options=sdk_options) as client:
                # Send query
                await client.query(full_prompt)
                
                # Receive and process messages
                async for msg in client.receive_messages():
                    # Process different message types
                    if isinstance(msg, AssistantMessage):
                        for block in msg.content:
                            if isinstance(block, TextBlock):
                                # Send text message (avoid duplicates)
                                text_hash = hashlib.md5(block.text.encode()).hexdigest()
                                if text_hash not in sent_text_hashes:
                                    sent_text_hashes.add(text_hash)
                                    yield {
                                        "type": "text",
                                        "content": block.text,
                                    }
                            
                            elif isinstance(block, ToolUseBlock):
                                # Send tool use message
                                if block.id not in sent_tool_ids:
                                    sent_tool_ids.add(block.id)
                                    yield {
                                        "type": "tool_use",
                                        "id": block.id,
                                        "name": block.name,
                                        "input": block.input,
                                    }
                            
                            elif isinstance(block, ThinkingBlock):
                                # Send thinking message
                                yield {
                                    "type": "thinking",
                                    "content": block.thinking,
                                }
                    
                    # Process user messages (tool results)
                    elif isinstance(msg, UserMessage):
                        for block in msg.content:
                            if isinstance(block, ToolResultBlock):
                                # Send tool result message
                                logger.info(f"Tool result for: {block.tool_use_id}")
                                
                                # Format output (handle both string and structured content)
                                output = block.content
                                if not isinstance(output, str):
                                    import json
                                    output = json.dumps(output)
                                
                                yield {
                                    "type": "tool_result",
                                    "toolUseId": block.tool_use_id,
                                    "output": output,
                                    "isError": block.is_error or False,
                                }
                    
                    elif isinstance(msg, SystemMessage):
                        # Send system message
                        yield {
                            "type": "system",
                            "subtype": msg.subtype,
                            "data": msg.data,
                        }
                    
                    elif isinstance(msg, ResultMessage):
                        # Send completion message
                        yield {
                            "type": "complete",
                            "sessionId": msg.session_id,
                            "durationMs": msg.duration_ms,
                            "numTurns": msg.num_turns,
                            "totalCostUsd": msg.total_cost_usd,
                        }
                        break
        
        except Exception as e:
            logger.error(f"Error running Claude Agent: {e}", exc_info=True)
            yield {
                "type": "error",
                "message": str(e),
            }
