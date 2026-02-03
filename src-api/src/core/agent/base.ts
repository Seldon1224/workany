/**
 * Agent SDK Abstraction Layer - Base Implementation
 *
 * Provides common functionality for all agent implementations.
 */

import { nanoid } from 'nanoid';

import type {
  AgentConfig,
  AgentMessage,
  AgentOptions,
  AgentProvider,
  AgentSession,
  IAgent,
  TaskPlan,
} from '@/core/agent/types';

import type { ProviderCapabilities } from '@/shared/provider/types';

/**
 * Agent capabilities interface
 */
export interface AgentCapabilities extends ProviderCapabilities {
  supportsPlan: boolean;
  supportsStreaming: boolean;
  supportsSandbox: boolean;
}

/**
 * Base class for agent implementations.
 * Provides common session management and plan storage.
 * Implements IProvider interface methods for compatibility.
 */
export abstract class BaseAgent implements IAgent {
  abstract readonly provider: AgentProvider;

  /** Provider type (alias for provider) */
  get type(): string {
    return this.provider;
  }

  /** Human-readable name */
  get name(): string {
    return `${this.provider} Agent`;
  }

  /** Provider version */
  readonly version: string = '1.0.0';

  protected config: AgentConfig;
  protected sessions: Map<string, AgentSession> = new Map();

  constructor(config: AgentConfig) {
    this.config = config;
  }

  /**
   * Create a new session
   */
  protected createSession(phase: AgentSession['phase'] = 'idle'): AgentSession {
    const session: AgentSession = {
      id: nanoid(),
      createdAt: new Date(),
      phase,
      isAborted: false,
      abortController: new AbortController(),
      config: this.config,
    };
    this.sessions.set(session.id, session);
    return session;
  }

  /**
   * Get an existing session
   */
  protected getSession(sessionId: string): AgentSession | undefined {
    return this.sessions.get(sessionId);
  }

  /**
   * Update session phase
   */
  protected updateSessionPhase(
    sessionId: string,
    phase: AgentSession['phase']
  ): void {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.phase = phase;
    }
  }



  /**
   * Stop execution for a session
   */
  async stop(sessionId: string): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.isAborted = true;
      session.abortController.abort();
    }
  }

  // ============================================================================
  // IProvider Interface Methods
  // ============================================================================

  /**
   * Check if this agent is available
   * Override in subclasses if specific checks are needed
   */
  async isAvailable(): Promise<boolean> {
    return true;
  }

  /**
   * Initialize the agent with configuration
   * Override in subclasses if initialization is needed
   */
  async init(config?: Record<string, unknown>): Promise<void> {
    if (config) {
      this.config = { ...this.config, ...config } as AgentConfig;
    }
  }

  /**
   * Shutdown the agent and cleanup resources
   */
  async shutdown(): Promise<void> {
    // Stop all active sessions
    for (const [sessionId, session] of this.sessions) {
      if (!session.isAborted) {
        await this.stop(sessionId);
      }
    }
    this.sessions.clear();
  }

  /**
   * Get agent capabilities
   * Override in subclasses to provide specific capabilities
   */
  getCapabilities(): AgentCapabilities {
    return {
      features: ['run', 'plan', 'execute', 'stop'],
      supportsPlan: true,
      supportsStreaming: true,
      supportsSandbox: false,
    };
  }

  /**
   * Clean up old sessions (call periodically)
   */
  protected cleanupSessions(maxAgeMs: number = 30 * 60 * 1000): void {
    const now = Date.now();
    for (const [id, session] of this.sessions) {
      if (now - session.createdAt.getTime() > maxAgeMs) {
        this.sessions.delete(id);
      }
    }
  }

  // Abstract method to be implemented by providers
  abstract run(
    prompt: string,
    options?: AgentOptions
  ): AsyncGenerator<AgentMessage>;
}



/**
 * Sandbox configuration for script execution
 */
export interface SandboxOptions {
  enabled: boolean;
  image?: string;
  apiEndpoint?: string;
}

/**
 * Generate workspace instruction for prompts
 */
export function getWorkspaceInstruction(
  workDir: string,
  sandbox?: SandboxOptions
): string {
  let instruction = `
## CRITICAL: Workspace Configuration
**MANDATORY OUTPUT DIRECTORY: ${workDir}**

ALL files you create MUST be saved to this directory. This is NON-NEGOTIABLE.

Rules:
1. ALWAYS use absolute paths starting with ${workDir}/
2. NEVER use any other directory (no ~/.claude/, no ~/Documents/, no /tmp/, no default paths)
3. NEVER use ~/pptx-workspace, ~/docx-workspace, ~/xlsx-workspace or similar
4. Scripts, documents, data files - EVERYTHING goes to ${workDir}/
5. Create subdirectories under ${workDir}/ if needed (e.g., ${workDir}/output/, ${workDir}/data/)

## CRITICAL: Read Before Write Rule
**ALWAYS use the Read tool before using the Write tool, even for new files.**
This is a security requirement. Before writing any file:
1. First, use the Read tool on the file path (it will show "file not found" for new files - this is expected)
2. Then, use the Write tool to create/update the file

Example workflow for creating a new file:
1. Read("${workDir}/script.py")  -> Returns error "file not found" (OK, this is expected)
2. Write("${workDir}/script.py", content)  -> Now this will succeed

## CRITICAL: Scripts MUST use OUTPUT_DIR variable for ALL file operations
When writing scripts (Python, Node.js, etc.), you MUST:
1. Define the output directory at the top of the script: \`OUTPUT_DIR = "${workDir}"\`
2. **ALWAYS create the output directory first** with os.makedirs (Python) or fs.mkdirSync (Node.js)
3. Use the OUTPUT_DIR variable (with os.path.join or path.join) for EVERY file read/write operation
4. NEVER hardcode any path - always use OUTPUT_DIR
5. NEVER use relative paths
6. NEVER use "/workspace" or any other hardcoded path

**CRITICAL**: Use OUTPUT_DIR consistently throughout the ENTIRE script. Do not define it at the top and then forget to use it later!

Python script example:
\`\`\`python
import os
OUTPUT_DIR = "${workDir}"

# IMPORTANT: Always create the output directory first!
os.makedirs(OUTPUT_DIR, exist_ok=True)

# CORRECT: Always use OUTPUT_DIR with os.path.join
output_file = os.path.join(OUTPUT_DIR, "results.json")
with open(output_file, "w") as f:
    f.write(data)

# WRONG examples (NEVER do these):
# with open("results.json", "w") as f:  # relative path
# with open("/workspace/results.json", "w") as f:  # hardcoded path
# output_file = "/workspace/results.txt"  # hardcoded path
\`\`\`

Node.js script example:
\`\`\`javascript
const fs = require('fs');
const path = require('path');
const OUTPUT_DIR = "${workDir}";

// IMPORTANT: Always create the output directory first!
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

// CORRECT: Always use OUTPUT_DIR with path.join
const outputFile = path.join(OUTPUT_DIR, "results.json");
fs.writeFileSync(outputFile, data);

// WRONG examples (NEVER do these):
// fs.writeFileSync("results.json", data);  # relative path
// fs.writeFileSync("/workspace/results.json", data);  # hardcoded path
\`\`\`

Examples:
- Script: "${workDir}/crawler.py" (NOT ~/script.py)
- Output: "${workDir}/results.json" (NOT /tmp/results.json)
- Document: "${workDir}/report.docx" (NOT ~/docx-workspace/report.docx)

## ⛔ MANDATORY: BACKUP BEFORE ANY DESTRUCTIVE OPERATION

**THIS IS NON-NEGOTIABLE. FAILURE TO BACKUP IS A CRITICAL ERROR.**

Before executing ANY of these operations, you MUST backup files FIRST:
- ❌ rm / rm -rf / delete / 删除
- ❌ Overwriting files (Write tool on existing file)
- ❌ Edit tool modifications
- ❌ mv / move / 移动
- ❌ Clearing directories (清空)

### MANDATORY Backup Procedure (DO THIS FIRST!)

**Step 1: Create backup directory**
\`\`\`bash
mkdir -p "${workDir}/backup/"
\`\`\`

**Step 2: Copy ALL files to be affected**
\`\`\`bash
# For single file:
cp "/path/to/file.txt" "${workDir}/backup/file_$(date +%Y%m%d_%H%M%S).txt"

# For directory:
cp -r "/path/to/folder" "${workDir}/backup/folder_$(date +%Y%m%d_%H%M%S)"
\`\`\`

**Step 3: ONLY THEN proceed with the destructive operation**

### Example: User asks "清空桌面" (clear desktop)

CORRECT execution order:
\`\`\`bash
# 1. First, create backup directory
mkdir -p "${workDir}/backup/"

# 2. Backup ALL desktop files
cp -r ~/Desktop/* "${workDir}/backup/desktop_backup_$(date +%Y%m%d_%H%M%S)/"

# 3. ONLY NOW delete
rm -rf ~/Desktop/*
\`\`\`

WRONG (NEVER DO THIS):
\`\`\`bash
# ❌ WRONG: Deleting without backup first
rm -rf ~/Desktop/*
\`\`\`

### What REQUIRES backup:
- ✅ Deleting files or folders (rm, delete, 删除, 清空)
- ✅ Modifying existing files (Edit, Write to existing)
- ✅ Moving files (backup source before mv)
- ✅ Renaming files

### What does NOT require backup:
- Creating NEW files (nothing to backup)
- Reading files (non-destructive)

### Additional Safety for Files Outside Workspace (${workDir}/)

For paths NOT under ${workDir}/, also ask user confirmation first:
- ~/Desktop/, ~/Documents/, ~/Downloads/
- System paths: /etc/, /usr/, /var/
- Any absolute path outside workspace

## 🖼️ Image Recognition Tool

**RecognizeImage Tool** is available for analyzing images:
- Supports: PNG, JPG, JPEG, GIF, WEBP
- Max file size: 5MB
- Use absolute paths to image files

**Example:**
\`\`\`
RecognizeImage({
  imagePath: "/absolute/path/to/image.png",
  question: "请识别验证码" // Optional
})
\`\`\`

## 🌐 Playwright Screenshot Best Practices

**CRITICAL: When using browser_take_screenshot from Playwright MCP:**

1. **Use RELATIVE filenames only** (no paths):
   \`\`\`
   ✅ CORRECT: filename: "captcha.png"
   ❌ WRONG:   filename: "/full/path/captcha.png"
   \`\`\`

2. **Playwright saves to:** \`.playwright-mcp/\` subdirectory automatically

3. **Complete workflow for captcha recognition:**
   \`\`\`
   Step 1: Take screenshot with relative filename
   browser_take_screenshot({
     element: "验证码图片",
     filename: "captcha.png"  // ✅ Relative name only
   })
   
   Step 2: Get full path from response
   // Playwright returns: .playwright-mcp/captcha.png
   
   Step 3: Use RecognizeImage with absolute path
   RecognizeImage({
     imagePath: "${workDir}/.playwright-mcp/captcha.png"
   })
   \`\`\`

**Why this matters:**
- Playwright MCP enforces security by restricting file writes to \`.playwright-mcp/\` directory
- Using absolute paths will cause: "Error: Resolved file path is outside of the output directory"
- Always use relative filenames and let Playwright handle the directory structure
`;

  // Add sandbox instructions when enabled
  if (sandbox?.enabled) {
    instruction += `
## Sandbox Mode (ENABLED)
Sandbox mode is enabled. You MUST use sandbox tools for running scripts.

**CRITICAL: PREFER Node.js SCRIPTS**
The app has a built-in Node.js runtime, but Python requires users to install it separately.
- **ALWAYS prefer writing Node.js (.js) scripts** over Python scripts
- Node.js standard library is powerful enough for most tasks (fs, path, http, https, crypto, child_process, etc.)
- Only use Python if the task specifically requires Python-only libraries (numpy, pandas, etc.)

**CRITICAL RULES**:
1. ALWAYS use \`sandbox_run_script\` to run scripts (Node.js, Python, TypeScript, etc.)
2. NEVER use Bash tool to run scripts directly (no \`node script.js\`, no \`python script.py\`)
3. After sandbox_run_script succeeds, the task is COMPLETE - do NOT run the script again with Bash
4. Scripts MUST use OUTPUT_DIR = "${workDir}" for all file operations

**Workflow**:
1. Create script file using Write tool (prefer .js files)
2. Use \`sandbox_run_script\` to execute it - THIS IS THE ONLY WAY TO RUN SCRIPTS
3. Script execution is DONE after sandbox_run_script returns

Example (Node.js - PREFERRED):
\`\`\`
sandbox_run_script:
  filePath: "${workDir}/script.js"
  workDir: "${workDir}"
  packages: ["axios"]  # optional npm packages
\`\`\`

Example (Python - only if necessary):
\`\`\`
sandbox_run_script:
  filePath: "${workDir}/script.py"
  workDir: "${workDir}"
  packages: ["requests"]  # optional pip packages
\`\`\`

**DO NOT** run the same script twice. Once sandbox_run_script completes successfully, move on to the next step.

`;
  }

  return instruction;
}




