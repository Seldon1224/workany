/**
 * Agent Service
 *
 * This service provides the main interface for running AI agents.
 * It uses the agents abstraction layer to support multiple providers.
 */

import {
  createAgent,
  createAgentFromEnv,
  type AgentConfig,
  type AgentMessage,
  type AgentSession,
  type ConversationMessage,
  type IAgent,
  type ImageAttachment,
  type McpConfig,
  type SandboxConfig,
  type SkillsConfig,
  type TaskPlan,
} from '@/core/agent';
// ============================================================================
// Logging - uses shared logger (writes to ~/.workany/logs/workany.log)
// ============================================================================
import { createLogger } from '@/shared/utils/logger';

const serviceLogger = createLogger('AgentService');

// Global agent instance (lazy initialized)
let globalAgent: IAgent | null = null;

// Store active sessions for backward compatibility
const activeSessions = new Map<string, { abortController: AbortController }>();

/**
 * Get or create the global agent instance
 * If modelConfig is provided, creates a new agent with those settings
 */
export function getAgent(config?: Partial<AgentConfig>): IAgent {
  console.log('[AgentService] getAgent called with config:', {
    hasConfig: !!config,
    hasApiKey: !!config?.apiKey,
    hasBaseUrl: !!config?.baseUrl,
    model: config?.model,
  });

  // If config with API credentials is provided, create a new agent instance
  // Don't cache it to allow different configs per request
  if (config && (config.apiKey || config.baseUrl || config.model)) {
    console.log('[AgentService] Creating new agent with custom config:', {
      hasApiKey: !!config.apiKey,
      baseUrl: config.baseUrl,
      model: config.model,
    });
    return createAgent({ provider: 'claude', ...config });
  }

  // Use cached global agent for default configuration
  if (!globalAgent || config) {
    console.log('[AgentService] Creating agent from environment variables');
    globalAgent = config
      ? createAgent({ provider: 'claude', ...config })
      : createAgentFromEnv();
  }
  return globalAgent;
}

/**
 * Create a new agent session
 */
export function createSession(): AgentSession {
  const session: AgentSession = {
    id: Date.now().toString(),
    createdAt: new Date(),
    phase: 'executing',
    isAborted: false,
    abortController: new AbortController(),
  };
  activeSessions.set(session.id, {
    abortController: session.abortController,
  });
  return session;
}

/**
 * Get an existing session
 */
export function getSession(sessionId: string): AgentSession | undefined {
  const session = activeSessions.get(sessionId);
  if (!session) return undefined;

  return {
    id: sessionId,
    createdAt: new Date(),
    phase: 'idle',
    isAborted: session.abortController.signal.aborted,
    abortController: session.abortController,
  };
}

/**
 * Delete a session
 */
export function deleteSession(sessionId: string): boolean {
  const session = activeSessions.get(sessionId);
  if (session) {
    session.abortController.abort();
    activeSessions.delete(sessionId);
    return true;
  }
  return false;
}

/**
 * Run agent directly (uses Claude Agent SDK's built-in task planning)
 */
export async function* runAgent(
  prompt: string,
  session: AgentSession,
  conversation?: ConversationMessage[],
  workDir?: string,
  taskId?: string,
  modelConfig?: { apiKey?: string; baseUrl?: string; model?: string },
  sandboxConfig?: SandboxConfig,
  images?: ImageAttachment[],
  skillsConfig?: SkillsConfig,
  mcpConfig?: McpConfig
): AsyncGenerator<AgentMessage> {
  const agent = getAgent(modelConfig);

  // Log sandbox config for debugging - write to file for packaged app visibility
  serviceLogger.info('[AgentService] runAgent called with sandbox config:', {
    hasSandboxConfig: !!sandboxConfig,
    sandboxEnabled: sandboxConfig?.enabled,
    sandboxProvider: sandboxConfig?.provider,
    apiEndpoint: sandboxConfig?.apiEndpoint,
  });
  serviceLogger.info('[AgentService] runAgent called with skills config:', skillsConfig);
  serviceLogger.info('[AgentService] runAgent called with mcp config:', mcpConfig);

  for await (const message of agent.run(prompt, {
    sessionId: session.id,
    conversation,
    cwd: workDir,
    taskId,
    abortController: session.abortController,
    sandbox: sandboxConfig,
    images,
    skillsConfig,
    mcpConfig,
  })) {
    yield message;
  }
}

/**
 * Stop an agent execution
 */
export function stopAgent(sessionId: string): void {
  const session = activeSessions.get(sessionId);
  if (session) {
    session.abortController.abort();
  }
}

// Re-export types for convenience
export type {
  AgentMessage,
  AgentSession,
  ConversationMessage,
  AgentConfig,
  IAgent,
  ImageAttachment,
  SkillsConfig,
  McpConfig,
};
