"""Agent API routes."""
import json
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from shared.services.agent import (
    create_session,
    delete_session,
    get_session,
    run_agent,
)
from shared.types.agent import (
    ConversationMessage,
    ImageAttachment,
    McpConfig,
    SandboxConfig,
    SkillsConfig,
)

router = APIRouter()


class ModelConfig(BaseModel):
    """Model configuration."""
    apiKey: Optional[str] = None
    baseUrl: Optional[str] = None
    model: Optional[str] = None


class AgentRequest(BaseModel):
    """Agent execution request."""
    prompt: str
    conversation: Optional[list[ConversationMessage]] = None
    workDir: Optional[str] = None
    taskId: Optional[str] = None
    modelConfig: Optional[ModelConfig] = None
    sandboxConfig: Optional[SandboxConfig] = None
    images: Optional[list[ImageAttachment]] = None
    skillsConfig: Optional[SkillsConfig] = None
    mcpConfig: Optional[McpConfig] = None


async def create_sse_stream(prompt: str, request: AgentRequest):
    """Create SSE stream for agent execution.
    
    Args:
        prompt: User prompt
        request: Agent request
    
    Yields:
        SSE formatted messages
    """
    session = create_session()
    
    # Convert ModelConfig to dict
    model_config_dict = None
    if request.modelConfig:
        model_config_dict = request.modelConfig.model_dump()
    
    try:
        async for message in run_agent(
            prompt=prompt,
            session=session,
            conversation=request.conversation,
            work_dir=request.workDir,
            task_id=request.taskId,
            model_config=model_config_dict,
            sandbox_config=request.sandboxConfig,
            images=request.images,
            skills_config=request.skillsConfig,
            mcp_config=request.mcpConfig,
        ):
            # Format as SSE
            data = json.dumps(message)
            yield f"data: {data}\n\n"
    except Exception as e:
        # Send error message
        error_data = json.dumps({
            "type": "error",
            "message": str(e),
        })
        yield f"data: {error_data}\n\n"


@router.post("/")
async def execute_agent(request: AgentRequest):
    """Execute agent with the given prompt.
    
    Args:
        request: Agent execution request
    
    Returns:
        SSE stream of agent messages
    """
    return StreamingResponse(
        create_sse_stream(request.prompt, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/stop/{session_id}")
async def stop_agent_execution(session_id: str):
    """Stop a running agent.
    
    Args:
        session_id: Session ID to stop
    
    Returns:
        Status message
    """
    session = get_session(session_id)
    if not session:
        return {"error": "Session not found"}, 404
    
    delete_session(session_id)
    return {"status": "stopped"}


@router.get("/session/{session_id}")
async def get_agent_session(session_id: str):
    """Get session status.
    
    Args:
        session_id: Session ID
    
    Returns:
        Session information
    """
    session = get_session(session_id)
    if not session:
        return {"error": "Session not found"}, 404
    
    return {
        "id": session.id,
        "createdAt": session.created_at.isoformat(),
        "phase": session.phase,
        "isAborted": session.is_aborted,
    }
