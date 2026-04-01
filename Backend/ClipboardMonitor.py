"""
Clipboard Monitor for O.R.A.N.G.E.S.
Monitors clipboard changes and writes detected content to a data file
for the GUI to display action suggestions.
"""

import time
import re
from Config import TempDirectoryPath

# Try to use pyperclip, fall back to tkinter
try:
    import pyperclip
    
    def get_clipboard():
        try:
            return pyperclip.paste()
        except:
            return ""
except ImportError:
    print("[WARN] pyperclip not installed, using tkinter fallback for clipboard")
    try:
        import tkinter as tk
        
        def get_clipboard():
            try:
                root = tk.Tk()
                root.withdraw()
                content = root.clipboard_get()
                root.destroy()
                return content
            except:
                return ""
    except:
        def get_clipboard():
            return ""


# Clipboard content type detection
def detect_content_type(text):
    """Detect what kind of content is on the clipboard.
    
    Returns:
        tuple: (type_str, preview_str)
    """
    if not text or not text.strip():
        return "empty", ""
    
    text = text.strip()
    
    # URL detection
    url_pattern = r'https?://[^\s]+'
    if re.match(url_pattern, text):
        return "url", text[:80]
    
    # Code detection (multiple heuristics)
    code_indicators = [
        'def ', 'class ', 'import ', 'from ', 'return ',  # Python
        'function ', 'const ', 'let ', 'var ', '=>',       # JavaScript
        '#include', 'int main', 'void ',                    # C/C++
        'public class', 'private ', 'protected ',           # Java
        '{', '}', '();', '[];',                             # General syntax
    ]
    
    lines = text.split('\n')
    code_score = sum(1 for indicator in code_indicators if indicator in text)
    if code_score >= 2 or (len(lines) > 3 and any(line.startswith('  ') or line.startswith('\t') for line in lines)):
        preview = text[:100].replace('\n', ' ')
        return "code", preview
    
    # Long text (potential article/paragraph)
    if len(text) > 200:
        preview = text[:100] + "..."
        return "text", preview
    
    # Short text
    return "text", text[:80]


def clipboard_monitor_loop(poll_interval=1.0):
    """Main monitoring loop. Runs in a daemon thread.
    
    Writes clipboard state to Clipboard.data in format:
    type|preview|full_content_hash
    
    Only writes when clipboard content actually changes.
    """
    last_content = ""
    
    while True:
        try:
            current = get_clipboard()
            
            # Only act on changes
            if current and current != last_content:
                last_content = current
                content_type, preview = detect_content_type(current)
                
                if content_type != "empty":
                    # Write to data file for GUI to read
                    data = f"{content_type}|{preview}|{len(current)}"
                    with open(TempDirectoryPath('Clipboard.data'), 'w', encoding='utf-8') as f:
                        f.write(data)
                    
                    print(f"[DEBUG] Clipboard changed: type={content_type}, len={len(current)}")
            
            time.sleep(poll_interval)
            
        except Exception as e:
            # Silently continue on errors (clipboard access can be flaky)
            time.sleep(poll_interval)


def get_clipboard_content():
    """Get the current clipboard content (for use when user acts on clipboard toast).
    
    Returns:
        str: The clipboard text content.
    """
    return get_clipboard()
