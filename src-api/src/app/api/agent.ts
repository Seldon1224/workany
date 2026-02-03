import { Hono } from 'hono';

import {
  createSession,
  deleteSession,
  getSession,
  runAgent,
} from '@/shared/services/agent';
import type { AgentRequest } from '@/shared/types/agent';

const agent = new Hono();

// Helper to create SSE stream
function createSSEStream(generator: AsyncGenerator<unknown>) {
  const encoder = new TextEncoder();
  return new ReadableStream({
    async start(controller) {
      try {
        for await (const message of generator) {
          const data = `data: ${JSON.stringify(message)}\n\n`;
          controller.enqueue(encoder.encode(data));
        }
      } catch (error) {
        const errorData = `data: ${JSON.stringify({
          type: 'error',
          message: error instanceof Error ? error.message : String(error),
        })}\n\n`;
        controller.enqueue(encoder.encode(errorData));
      } finally {
        controller.close();
      }
    },
  });
}

// SSE Response headers
const SSE_HEADERS = {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache, no-transform',
  Connection: 'keep-alive',
  'X-Accel-Buffering': 'no',
};

// Direct execution - Claude Agent SDK handles task planning internally
agent.post('/', async (c) => {
  const body = await c.req.json<AgentRequest>();

  console.log('[AgentAPI] POST / received:', {
    hasPrompt: !!body.prompt,
    hasModelConfig: !!body.modelConfig,
    modelConfig: body.modelConfig
      ? {
          hasApiKey: !!body.modelConfig.apiKey,
          baseUrl: body.modelConfig.baseUrl,
          model: body.modelConfig.model,
        }
      : null,
    sandboxConfig: body.sandboxConfig
      ? {
          enabled: body.sandboxConfig.enabled,
          provider: body.sandboxConfig.provider,
        }
      : null,
    hasImages: !!body.images,
    imagesCount: body.images?.length || 0,
  });

  // Debug logging for images
  if (body.images && body.images.length > 0) {
    body.images.forEach(
      (img: { data: string; mimeType: string }, i: number) => {
        console.log(
          `[AgentAPI] Image ${i}: mimeType=${img.mimeType}, dataLength=${img.data?.length || 0}`
        );
      }
    );
  } else {
    console.log('[AgentAPI] No images in request');
  }

  if (!body.prompt) {
    return c.json({ error: 'prompt is required' }, 400);
  }

  const session = createSession();
  const readable = createSSEStream(
    runAgent(
      body.prompt,
      session,
      body.conversation,
      body.workDir,
      body.taskId,
      body.modelConfig,
      body.sandboxConfig,
      body.images,
      body.skillsConfig,
      body.mcpConfig
    )
  );

  return new Response(readable, { headers: SSE_HEADERS });
});

// Stop a running agent
agent.post('/stop/:sessionId', async (c) => {
  const sessionId = c.req.param('sessionId');
  const session = getSession(sessionId);

  if (!session) {
    return c.json({ error: 'Session not found' }, 404);
  }

  deleteSession(sessionId);
  return c.json({ status: 'stopped' });
});

// Get session status
agent.get('/session/:sessionId', async (c) => {
  const sessionId = c.req.param('sessionId');
  const session = getSession(sessionId);

  if (!session) {
    return c.json({ error: 'Session not found' }, 404);
  }

  return c.json({
    id: session.id,
    createdAt: session.createdAt,
    phase: session.phase,
    isAborted: session.abortController.signal.aborted,
  });
});

export default agent;
