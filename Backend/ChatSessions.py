"""
Chat Sessions Manager for O.R.A.N.G.E.S.
Handles creating new chat sessions, archiving old ones, and listing/loading archived sessions.
"""

import os
import json
import shutil
from datetime import datetime
from Config import DataDirectoryPath

# Archive directory
ARCHIVE_DIR = DataDirectoryPath('ChatArchive')
ACTIVE_SESSION_FILE = DataDirectoryPath('ActiveSession.txt')


def _ensure_archive_dir():
    """Create the archive directory if it doesn't exist."""
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)


def create_new_session():
    """Archive the current ChatLog.json and start a fresh conversation.
    
    Returns:
        str: The filename of the archived session, or None if chat was empty.
    """
    _ensure_archive_dir()
    
    chatlog_path = DataDirectoryPath('ChatLog.json')
    
    try:
        # Read current chat log
        with open(chatlog_path, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        # Only archive if there are actual messages
        if messages and len(messages) > 0:
            # Prevent duplicates: Find if this chat is a continuation of an existing archive
            # Read active session ID
            existing_match_file = None
            existing_title = None
            
            try:
                if os.path.exists(ACTIVE_SESSION_FILE):
                    with open(ACTIVE_SESSION_FILE, 'r') as f:
                        active_file = f.read().strip()
                    if active_file and active_file.endswith('.json'):
                        # Verify the file still exists in archive
                        filepath = os.path.join(ARCHIVE_DIR, active_file)
                        if os.path.exists(filepath):
                            with open(filepath, 'r', encoding='utf-8') as f:
                                old_data = json.load(f)
                            existing_match_file = active_file
                            existing_title = old_data.get('title', 'Unknown Chat')
            except Exception as e:
                print(f"[DEBUG] Error reading active session: {e}")
            
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            
            if existing_match_file:
                # Overwrite the existing file to prevent duplicates
                archive_filename = existing_match_file
                archive_path = os.path.join(ARCHIVE_DIR, archive_filename)
                final_title = existing_title
                print(f"[DEBUG] Updating existing chat archive: {archive_filename}")
            else:
                # Completely new chat, generate a title
                archive_filename = f"chat_{timestamp}.json"
                archive_path = os.path.join(ARCHIVE_DIR, archive_filename)
                
                # Get first user message content
                first_msg = ""
                for msg in messages:
                    if msg.get("role") == "user":
                        first_msg = msg.get("content", "")
                        break
                
                # Generate 2-4 word title using Groq
                try:
                    from groq import Groq
                    from dotenv import dotenv_values
                    env_dict = dotenv_values(".env")
                    client = Groq(api_key=env_dict.get("GROQ_API_KEY"))
                    resp = client.chat.completions.create(
                        model='llama-3.3-70b-versatile',
                        messages=[
                            {"role": "system", "content": "Summarize the user's message into a compact 2, 3, or 4 word title. NO quotes, NO explanation, NO punctuation. Just the title words."},
                            {"role": "user", "content": first_msg[:500]}
                        ],
                        max_tokens=10,
                        temperature=0.3
                    )
                    final_title = resp.choices[0].message.content.strip().replace('"', '').replace("'", "")
                    if len(final_title.split()) > 6:  # Fallback if API disobeys
                        final_title = first_msg[:30] + "..."
                except Exception as e:
                    print(f"[WARN] Failed to generate title, using fallback: {e}")
                    final_title = first_msg[:30] + "..." if first_msg else "Untitled Chat"
                
                print(f"[DEBUG] Created new chat archive: {archive_filename}")
            
            # Save with metadata
            archive_data = {
                "timestamp": timestamp,
                "title": final_title,
                "message_count": len(messages),
                "messages": messages
            }
            
            with open(archive_path, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, indent=4, ensure_ascii=False)
        
        # Clear current chat log and reset active session pointer
        with open(chatlog_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        with open(ACTIVE_SESSION_FILE, 'w') as f:
            f.write('')
        
        print(f"[DEBUG] New chat session initialized (was tracking: {archive_filename})")
        return archive_filename
        
    except FileNotFoundError:
        # No existing chat log — just create an empty one
        with open(chatlog_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return None
    except Exception as e:
        print(f"[ERROR] Error creating new session: {e}")
        import traceback
        traceback.print_exc()
        return None


def list_sessions():
    """List all archived chat sessions.
    
    Returns:
        list[dict]: List of session info dicts with keys: filename, timestamp, title, message_count
    """
    _ensure_archive_dir()
    
    sessions = []
    try:
        for filename in sorted(os.listdir(ARCHIVE_DIR), reverse=True):
            if filename.endswith('.json'):
                filepath = os.path.join(ARCHIVE_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    sessions.append({
                        "filename": filename,
                        "timestamp": data.get("timestamp", "Unknown"),
                        "title": data.get("title", "Untitled"),
                        "message_count": data.get("message_count", 0)
                    })
                except Exception as e:
                    print(f"[WARN] Could not read archive {filename}: {e}")
    except Exception as e:
        print(f"[ERROR] Error listing sessions: {e}")
    
    return sessions


def load_session(filename):
    """Load an archived session back into the active ChatLog.json.
    
    Args:
        filename: The archive filename to load (e.g., 'chat_2026-03-18_22-40-00.json')
    
    Returns:
        bool: True if session was loaded successfully.
    """
    archive_path = os.path.join(ARCHIVE_DIR, filename)
    chatlog_path = DataDirectoryPath('ChatLog.json')
    
    try:
        # First archive the current session (if any)
        create_new_session()
        
        # Load the archived session
        with open(archive_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages = data.get("messages", [])
        
        # Write to current chat log
        with open(chatlog_path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=4, ensure_ascii=False)
            
        # Update active session pointer
        with open(ACTIVE_SESSION_FILE, 'w') as f:
            f.write(filename)
            
        # Reconstruct Responses.data for GUI to parse
        from Config import TempDirectoryPath
        from dotenv import dotenv_values
        env = dotenv_values(".env")
        usr = env.get("Username", "User")
        ast = env.get("Assistantname", "O.R.A.N.G.E.S")
        
        responses_text = ""
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                responses_text += f"{usr} : {content}\n"
            else:
                responses_text += f"{ast} : {content}\n"
                
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as f:
            f.write(responses_text)
            
        print(f"[DEBUG] Loaded session: {filename} ({len(messages)} messages)")
        return True
        
    except FileNotFoundError:
        print(f"[ERROR] Archive not found: {filename}")
        return False
    except Exception as e:
        print(f"[ERROR] Error loading session: {e}")
        import traceback
        traceback.print_exc()
        return False


def delete_session(filename):
    """Delete an archived session.
    
    Args:
        filename: The archive filename to delete.
    
    Returns:
        bool: True if deleted successfully.
    """
    archive_path = os.path.join(ARCHIVE_DIR, filename)
    
    try:
        if os.path.exists(archive_path):
            os.remove(archive_path)
            print(f"[DEBUG] Deleted session: {filename}")
            return True
        else:
            print(f"[WARN] Session not found: {filename}")
            return False
    except Exception as e:
        print(f"[ERROR] Error deleting session: {e}")
        return False

def rename_session(filename, new_title):
    """Rename an archived session's title.
    
    Args:
        filename: The archive filename
        new_title: The new title for the chat
    """
    archive_path = os.path.join(ARCHIVE_DIR, filename)
    try:
        with open(archive_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data['title'] = new_title
        
        with open(archive_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"[DEBUG] Renamed session {filename} to '{new_title}'")
        return True
    except Exception as e:
        print(f"[ERROR] Error renaming session: {e}")
        return False
