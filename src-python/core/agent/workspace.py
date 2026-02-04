"""Workspace instruction generator for Claude Agent."""
from typing import Optional

from shared.types.agent import SandboxConfig


def get_workspace_instruction(
    work_dir: str,
    sandbox: Optional[SandboxConfig] = None
) -> str:
    """Generate workspace instruction for prompts.
    
    Args:
        work_dir: Working directory path
        sandbox: Optional sandbox configuration
    
    Returns:
        Workspace instruction string
    """
    instruction = f"""
## CRITICAL: Workspace Configuration
**MANDATORY OUTPUT DIRECTORY: {work_dir}**

ALL files you create MUST be saved to this directory. This is NON-NEGOTIABLE.

Rules:
1. ALWAYS use absolute paths starting with {work_dir}/
2. NEVER use any other directory (no ~/.claude/, no ~/Documents/, no /tmp/, no default paths)
3. NEVER use ~/pptx-workspace, ~/docx-workspace, ~/xlsx-workspace or similar
4. Scripts, documents, data files - EVERYTHING goes to {work_dir}/
5. Create subdirectories under {work_dir}/ if needed (e.g., {work_dir}/output/, {work_dir}/data/)

## CRITICAL: Read Before Write Rule
**ALWAYS use the Read tool before using the Write tool, even for new files.**
This is a security requirement. Before writing any file:
1. First, use the Read tool on the file path (it will show "file not found" for new files - this is expected)
2. Then, use the Write tool to create/update the file

Example workflow for creating a new file:
1. Read("{work_dir}/script.py")  -> Returns error "file not found" (OK, this is expected)
2. Write("{work_dir}/script.py", content)  -> Now this will succeed

## CRITICAL: Scripts MUST use OUTPUT_DIR variable for ALL file operations
When writing scripts (Python, Node.js, etc.), you MUST:
1. Define the output directory at the top of the script: `OUTPUT_DIR = "{work_dir}"`
2. **ALWAYS create the output directory first** with os.makedirs (Python) or fs.mkdirSync (Node.js)
3. Use the OUTPUT_DIR variable (with os.path.join or path.join) for EVERY file read/write operation
4. NEVER hardcode any path - always use OUTPUT_DIR
5. NEVER use relative paths
6. NEVER use "/workspace" or any other hardcoded path

**CRITICAL**: Use OUTPUT_DIR consistently throughout the ENTIRE script. Do not define it at the top and then forget to use it later!

Python script example:
```python
import os
OUTPUT_DIR = "{work_dir}"

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
```

Node.js script example:
```javascript
const fs = require('fs');
const path = require('path');
const OUTPUT_DIR = "{work_dir}";

// IMPORTANT: Always create the output directory first!
fs.mkdirSync(OUTPUT_DIR, {{ recursive: true }});

// CORRECT: Always use OUTPUT_DIR with path.join
const outputFile = path.join(OUTPUT_DIR, "results.json");
fs.writeFileSync(outputFile, data);

// WRONG examples (NEVER do these):
// fs.writeFileSync("results.json", data);  # relative path
// fs.writeFileSync("/workspace/results.json", data);  # hardcoded path
```

Examples:
- Script: "{work_dir}/crawler.py" (NOT ~/script.py)
- Output: "{work_dir}/results.json" (NOT /tmp/results.json)
- Document: "{work_dir}/report.docx" (NOT ~/docx-workspace/report.docx)

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
```bash
mkdir -p "{work_dir}/backup/"
```

**Step 2: Copy ALL files to be affected**
```bash
# For single file:
cp "/path/to/file.txt" "{work_dir}/backup/file_$(date +%Y%m%d_%H%M%S).txt"

# For directory:
cp -r "/path/to/folder" "{work_dir}/backup/folder_$(date +%Y%m%d_%H%M%S)"
```

**Step 3: ONLY THEN proceed with the destructive operation**

### Example: User asks "清空桌面" (clear desktop)

CORRECT execution order:
```bash
# 1. First, create backup directory
mkdir -p "{work_dir}/backup/"

# 2. Backup ALL desktop files
cp -r ~/Desktop/* "{work_dir}/backup/desktop_backup_$(date +%Y%m%d_%H%M%S)/"

# 3. ONLY NOW delete
rm -rf ~/Desktop/*
```

WRONG (NEVER DO THIS):
```bash
# ❌ WRONG: Deleting without backup first
rm -rf ~/Desktop/*
```

### What REQUIRES backup:
- ✅ Deleting files or folders (rm, delete, 删除, 清空)
- ✅ Modifying existing files (Edit, Write to existing)
- ✅ Moving files (backup source before mv)
- ✅ Renaming files

### What does NOT require backup:
- Creating NEW files (nothing to backup)
- Reading files (non-destructive)

### Additional Safety for Files Outside Workspace ({work_dir}/)

For paths NOT under {work_dir}/, also ask user confirmation first:
- ~/Desktop/, ~/Documents/, ~/Downloads/
- System paths: /etc/, /usr/, /var/
- Any absolute path outside workspace

## 🖼️ Image Recognition Tool

**RecognizeImage Tool** is available for analyzing images:
- Supports: PNG, JPG, JPEG, GIF, WEBP
- Max file size: 5MB
- Use absolute paths to image files

**Example:**
```
RecognizeImage({{
  imagePath: "/absolute/path/to/image.png",
  question: "请识别验证码" // Optional
}})
```

## 🌐 Playwright Screenshot Best Practices

**CRITICAL: When using browser_take_screenshot from Playwright MCP:**

1. **Recommended: Use full absolute paths**:
   ```
   ✅ RECOMMENDED: filename: "{work_dir}/.playwright-mcp/captcha.png"
   ⚠️  ACCEPTABLE:  filename: "captcha.png" (relative path)
   ```

2. **Playwright default save directory:** `.playwright-mcp/` subdirectory

3. **Complete workflow for captcha recognition:**
   ```
   Step 1: Take screenshot with full path
   browser_take_screenshot({{
     element: "captcha image selector",
     filename: "{work_dir}/.playwright-mcp/captcha.png"  // ✅ Use full path
   }})
   
   Step 2: Use the same path for image recognition
   RecognizeImage({{
     imagePath: "{work_dir}/.playwright-mcp/captcha.png"
   }})
   ```

**Why use full paths:**
- Explicitly specify file save location, avoiding path confusion
- Consistent path format with RecognizeImage tool
- Easier to track and manage screenshot files
- Playwright MCP automatically ensures files are saved in `.playwright-mcp/` directory
"""
    
    # Add sandbox instructions when enabled
    if sandbox and sandbox.enabled:
        instruction += f"""
## Sandbox Mode (ENABLED)
Sandbox mode is enabled. You MUST use sandbox tools for running scripts.

**CRITICAL: PREFER Node.js SCRIPTS**
The app has a built-in Node.js runtime, but Python requires users to install it separately.
- **ALWAYS prefer writing Node.js (.js) scripts** over Python scripts
- Node.js standard library is powerful enough for most tasks (fs, path, http, https, crypto, child_process, etc.)
- Only use Python if the task specifically requires Python-only libraries (numpy, pandas, etc.)

**CRITICAL RULES**:
1. ALWAYS use `sandbox_run_script` to run scripts (Node.js, Python, TypeScript, etc.)
2. NEVER use Bash tool to run scripts directly (no `node script.js`, no `python script.py`)
3. After sandbox_run_script succeeds, the task is COMPLETE - do NOT run the script again with Bash
4. Scripts MUST use OUTPUT_DIR = "{work_dir}" for all file operations

**Workflow**:
1. Create script file using Write tool (prefer .js files)
2. Use `sandbox_run_script` to execute it - THIS IS THE ONLY WAY TO RUN SCRIPTS
3. Script execution is DONE after sandbox_run_script returns

Example (Node.js - PREFERRED):
```
sandbox_run_script:
  filePath: "{work_dir}/script.js"
  workDir: "{work_dir}"
  packages: ["axios"]  # optional npm packages
```

Example (Python - only if necessary):
```
sandbox_run_script:
  filePath: "{work_dir}/script.py"
  workDir: "{work_dir}"
  packages: ["requests"]  # optional pip packages
```

**DO NOT** run the same script twice. Once sandbox_run_script completes successfully, move on to the next step.

"""
    
    return instruction
