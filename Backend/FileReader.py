"""
File Reader for O.R.A.N.G.E.S.
Reads content from various file types for the assistant to process.
"""

import os


# Supported file extensions and their handlers
SUPPORTED_EXTENSIONS = {
    '.txt', '.py', '.js', '.ts', '.json', '.md', '.csv',
    '.html', '.css', '.xml', '.yaml', '.yml', '.toml',
    '.ini', '.cfg', '.conf', '.log', '.sql', '.sh', '.bat',
    '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go',
    '.rs', '.rb', '.php', '.swift', '.kt', '.r',
    '.pdf'
}

# Maximum file size to read (in bytes) — 500KB
MAX_FILE_SIZE = 500 * 1024

# Maximum content length to send to AI (characters)
MAX_CONTENT_LENGTH = 5000


def read_file(filepath):
    """Read a file and return its content as text.
    
    Args:
        filepath: Absolute path to the file.
    
    Returns:
        tuple: (success: bool, content: str, filetype: str)
    """
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}", ""
    
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type: {ext}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}", ext
    
    # Check file size
    file_size = os.path.getsize(filepath)
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large ({file_size / 1024:.1f} KB). Maximum: {MAX_FILE_SIZE / 1024:.1f} KB", ext
    
    if file_size == 0:
        return False, "File is empty.", ext
    
    # Handle PDF files
    if ext == '.pdf':
        return _read_pdf(filepath)
    
    # Handle text files
    return _read_text_file(filepath)


def _read_text_file(filepath):
    """Read a plain text file with encoding detection."""
    ext = os.path.splitext(filepath)[1].lower()
    
    # Try multiple encodings
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'ascii']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Truncate if too long
            if len(content) > MAX_CONTENT_LENGTH:
                content = content[:MAX_CONTENT_LENGTH] + f"\n\n... (truncated, file has {len(content)} total characters)"
            
            return True, content, ext
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    return False, "Could not decode file with any supported encoding.", ext


def _read_pdf(filepath):
    """Read a PDF file and extract text."""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        return False, "PyPDF2 is not installed. Run: pip install PyPDF2", '.pdf'
    
    try:
        reader = PdfReader(filepath)
        text_parts = []
        
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"--- Page {i+1} ---\n{page_text}")
        
        if not text_parts:
            return False, "PDF has no extractable text (might be image-based).", '.pdf'
        
        content = "\n\n".join(text_parts)
        
        # Truncate if too long
        if len(content) > MAX_CONTENT_LENGTH:
            content = content[:MAX_CONTENT_LENGTH] + f"\n\n... (truncated, PDF has {len(reader.pages)} pages)"
        
        return True, content, '.pdf'
        
    except Exception as e:
        return False, f"Error reading PDF: {str(e)}", '.pdf'


def get_supported_extensions():
    """Return list of supported file extensions for drag-drop filtering."""
    return list(SUPPORTED_EXTENSIONS)
