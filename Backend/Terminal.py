"""
Terminal Command Execution for O.R.A.N.G.E.S.
Safely executes terminal/shell commands and returns their output.
"""

import subprocess
import re


# Dangerous commands that should NEVER be executed
BLOCKED_COMMANDS = [
    # Destructive file operations
    r'\brm\s+-rf\b', r'\brm\s+-r\b', r'\brm\s+/', r'\brmdir\s+/s\b',
    r'\bdel\s+/s\b', r'\bdel\s+/q\b', r'\bdel\s+\*', r'\brd\s+/s\b',
    r'\bformat\b', r'\bfdisk\b', r'\bmkfs\b',
    # System destruction
    r'\bshutdown\b', r'\breboot\b', r'\bhalt\b',
    r'\breg\s+delete\b', r'\bregedit\b',
    # Dangerous downloads/execution
    r'\bcurl\b.*\|\s*(bash|sh|python)', r'\bwget\b.*\|\s*(bash|sh|python)',
    r'\bpowershell\b.*-enc', r'\bInvoke-Expression\b',
    # Disk/partition
    r'\bdiskpart\b', r'\bdd\s+if=\b',
    # Permission escalation
    r'\bchmod\s+777\b', r'\bchown\s+-R\b',
    # Fork bombs
    r':\(\)\{', r'\bfork\b',
]

# Allowed safe command prefixes (whitelist approach for extra safety)
SAFE_PREFIXES = [
    'python', 'pip', 'node', 'npm', 'npx', 'git',
    'dir', 'ls', 'cat', 'type', 'echo', 'cd', 'pwd',
    'whoami', 'hostname', 'ipconfig', 'ifconfig',
    'ping', 'tracert', 'nslookup',
    'systeminfo', 'tasklist', 'wmic', 'ver',
    'where', 'which', 'find', 'findstr', 'grep',
    'tree', 'cls', 'clear', 'date', 'time',
    'set', 'env', 'printenv',
    'java', 'javac', 'gcc', 'g++', 'make', 'cmake',
    'docker', 'kubectl',
    'conda', 'virtualenv', 'venv',
    'curl', 'wget',  # Allowed standalone (blocked when piped to bash above)
]

# Maximum execution time (seconds)
MAX_TIMEOUT = 30

# Maximum output length (characters)
MAX_OUTPUT_LENGTH = 3000


def is_command_safe(cmd):
    """Check if a command is safe to execute.
    
    Args:
        cmd: The command string to check.
    
    Returns:
        tuple: (is_safe: bool, reason: str)
    """
    cmd_lower = cmd.lower().strip()
    
    # Check against blocked patterns
    for pattern in BLOCKED_COMMANDS:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            return False, f"Blocked: matches dangerous pattern '{pattern}'"
    
    # Check if command starts with a safe prefix
    first_word = cmd_lower.split()[0] if cmd_lower.split() else ""
    
    # Strip path prefixes (e.g., "C:\Python\python.exe" -> "python.exe" -> "python")
    first_word_base = first_word.split('\\')[-1].split('/')[-1]
    if '.' in first_word_base:
        first_word_base = first_word_base.rsplit('.', 1)[0]
    
    is_whitelisted = any(first_word_base.startswith(prefix) for prefix in SAFE_PREFIXES)
    
    if not is_whitelisted:
        # Allow it but warn — don't block unknown commands entirely
        return True, f"Warning: '{first_word}' is not in the safe command list. Proceeding with caution."
    
    return True, "OK"


def execute_command(cmd):
    """Execute a terminal command and return its output.
    
    Args:
        cmd: The command string to execute.
    
    Returns:
        str: The command output (stdout + stderr), or an error message.
    """
    if not cmd or not cmd.strip():
        return "Error: No command provided."
    
    # Safety check
    is_safe, reason = is_command_safe(cmd)
    if not is_safe:
        return f"⛔ Command blocked for safety: {reason}\nCommand: {cmd}"
    
    try:
        print(f"[DEBUG] Terminal executing: {cmd}")
        
        if reason != "OK":
            print(f"[WARN] Terminal safety: {reason}")
        
        # Execute the command
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=MAX_TIMEOUT,
            cwd=None,  # Use current working directory
            encoding='utf-8',
            errors='replace'
        )
        
        output_parts = []
        
        if result.stdout:
            output_parts.append(result.stdout)
        
        if result.stderr:
            output_parts.append(f"[stderr]\n{result.stderr}")
        
        if result.returncode != 0:
            output_parts.append(f"\n[Exit code: {result.returncode}]")
        
        output = "\n".join(output_parts) if output_parts else "(Command completed with no output)"
        
        # Truncate if too long
        if len(output) > MAX_OUTPUT_LENGTH:
            output = output[:MAX_OUTPUT_LENGTH] + f"\n\n... (output truncated, {len(output)} total characters)"
        
        print(f"[DEBUG] Terminal output length: {len(output)}")
        return output
        
    except subprocess.TimeoutExpired:
        return f"⏱️ Command timed out after {MAX_TIMEOUT} seconds.\nCommand: {cmd}"
    except FileNotFoundError:
        return f"❌ Command not found: {cmd.split()[0]}"
    except Exception as e:
        print(f"[ERROR] Terminal execution error: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ Error executing command: {str(e)}"
