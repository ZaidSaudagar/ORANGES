from AppOpener import open, close
import webbrowser
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import subprocess
import requests
import keyboard
import asyncio
import os
from Config import DataDirectoryPath
from Backend.Terminal import execute_command
from Backend.ScreenCapture import describe_screen

# Load environment variables from the .env file
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GROQ_API_KEY")  # ✅ Corrected key name

# Fallback error if API key is missing
if not GroqAPIKey:
    raise ValueError("❌ GROQ_API_KEY is not set in your .env file.")

# Define CSS classes used for parsing search HTML
classes = [
    "ZCubwf", "hgkEle", "LTK0O sV7ric", "ZOcLcw", "gsrt vk_bk FzVMSb YwPhnf",
    "pclqee", "tw-data-text tw-text-small tw-ta-", "IZ6rdc", "O5UR6d LTK0O", "vlzY6d",
    "webanswers-webanswers_table__webanswers-table", "dOOno lKbO0b gsrt", "sXLADe",
    "LwKfKe", "vQF4q", "qvJWpe", "kno-rdesc", "SPZ26b"
]

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

professional_responses = [
    "Your satisfaction is my top priority, Sir; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need—don't hesitate to ask."
]

# Limit messages list to prevent memory growth
MAX_MESSAGES = 20
messages = []

# ✅ Format system message using environment variable safely
SystemChatBot = [{
    "role": "system",
    "content": f"Hello, I am {env_vars.get('Username', 'User')}. You're a content writer. You have to write content like letters, codes, applications, essays, notes, songs, poems etc."
}]

def GoogleSearch(Topic):
    search(Topic)
    return "Opened Google Search"

def Content(Topic):
    def OpenNotepad(file):
        try:
            subprocess.Popen(['notepad.exe', file])
        except Exception as e:
            print(f"[ERROR] Failed to open notepad with file '{file}': {e}")

    def ContentWriterAI(prompt):
        # Limit messages list size to prevent memory growth
        if len(messages) > MAX_MESSAGES:
            messages[:] = messages[-MAX_MESSAGES:]
        
        messages.append({"role": "user", "content": prompt})

        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=SystemChatBot + messages,
                max_tokens=2048,
                temperature=0.7,
                top_p=1,
                stream=True,
                stop=None
            )

            Answer = ""
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    Answer += chunk.choices[0].delta.content

            Answer = Answer.replace("</s>", "")
            if Answer:
                messages.append({"role": "assistant", "content": Answer})
            return Answer
        except Exception as e:
            print(f"[ERROR] Error in ContentWriterAI: {e}")
            raise

    try:
        Topic = Topic.replace("Content ", "").strip()
        if not Topic:
            return "No content topic provided"
            
        ContentByAI = ContentWriterAI(Topic)
        
        if not ContentByAI:
            return "Failed to generate content"

        # Sanitize filename
        import re
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', Topic.lower().replace(' ', ''))
        if len(safe_filename) > 200:
            safe_filename = safe_filename[:200]
            
        filepath = DataDirectoryPath(f"{safe_filename}.txt")
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(ContentByAI)

        OpenNotepad(filepath)
        return f"Content generated: {safe_filename}"
    except Exception as e:
        print(f"[ERROR] Error in Content function: {e}")
        import traceback
        traceback.print_exc()
        return "Error creating content"

def YouTubeSearch(Topic):
    url = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(url)
    return f"Opened YouTube search for {Topic}"

def PlayYoutube(query):
    playonyt(query)
    return f"Playing {query} on YouTube"

def OpenApp(app, sess=requests.session()):
    try:
        open(app, match_closest=True, output=True, throw_error=True)
        return f"Opened {app}"
    except Exception as e:
        print(f"[DEBUG] AppOpener failed for '{app}', trying web search fallback: {e}")
        try:
            def extract_links(html):
                if html is None:
                    return []
                soup = BeautifulSoup(html, 'html.parser')
                links = soup.find_all('a', {'jsname': 'UWckNb'})
                return [link.get('href') for link in links if link.get('href')]

            def search_google(query):
                url = f"https://www.google.com/search?q={query}"
                headers = {"User-Agent": user_agent}
                response = sess.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    return response.text
                else:
                    return None

            html = search_google(app)
            links = extract_links(html)
            if links:
                webbrowser.open(links[0])
                return f"Opened {app} via Web"
            else:
                return f"Could not find {app}"
        except Exception as e2:
            return f"Failed to open {app}"

def CloseApp(app):
    if "chrome" in app.lower():
        return "Cannot close Chrome (Protected)"
    try:
        close(app, match_closest=True, output=True, throw_error=True)
        return f"Closed {app}"
    except Exception as e:
        return f"Failed to close {app}"

def System(command):
    def mute(): keyboard.press_and_release("volume mute")
    def unmute(): keyboard.press_and_release("volume unmute")
    def volume_up(): keyboard.press_and_release("volume up")
    def volume_down(): keyboard.press_and_release("volume down")
    
    command = command.lower().strip()
    
    if "mute" in command and "unmute" not in command:
        mute()
        return "System Muted"
    elif "unmute" in command:
        unmute()
        return "System Unmuted"
    elif "maximize" in command or "100%" in command:
        # Press volume up 50 times to maximize
        for _ in range(50):
            keyboard.press_and_release("volume up")
        return "System Volume Maximized"
    elif "volume up" in command or "increase" in command:
        for _ in range(5):
            volume_up()
        return "Volume Increased"
    elif "volume down" in command or "decrease" in command:
        for _ in range(5):
            volume_down()
        return "Volume Decreased"
    elif "shut down" in command or "shutdown" in command:
        os.system("shutdown /s /t 5")
        return "Shutting down system"
    elif "restart" in command:
        os.system("shutdown /r /t 5")
        return "Restarting system"
    elif "sleep" in command or "suspend" in command:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "Putting system to sleep"
        
    return f"Unknown system command: {command}"

async def TranslateAndExecute(commands: list[str]):
    funcs = []

    for command in commands:
        if command.startswith("open ") and "open it" not in command and command != "open file":
            funcs.append(asyncio.to_thread(OpenApp, command.removeprefix("open ")))
        elif command.startswith("close "):
            funcs.append(asyncio.to_thread(CloseApp, command.removeprefix("close ")))
        elif command.startswith("play "):
            funcs.append(asyncio.to_thread(PlayYoutube, command.removeprefix("play ")))
        elif command.startswith("content "):
            funcs.append(asyncio.to_thread(Content, command.removeprefix("content ")))
        elif command.startswith("google search "):
            funcs.append(asyncio.to_thread(GoogleSearch, command.removeprefix("google search ")))
        elif command.startswith("Youtube "):
            funcs.append(asyncio.to_thread(YouTubeSearch, command.removeprefix("Youtube ")))
        elif command.startswith("system "):
            funcs.append(asyncio.to_thread(System, command.removeprefix("system ")))
        elif command.startswith("run "):
            funcs.append(asyncio.to_thread(execute_command, command.removeprefix("run ")))
        elif command.startswith("screenshot"):
            query = command.removeprefix("screenshot").strip() or "Describe what you see on this screen."
            funcs.append(asyncio.to_thread(describe_screen, query))
        else:
            print(f"[red]No Function Found for: {command}[/red]")

    results = await asyncio.gather(*funcs)
    for result in results:
        yield result

async def Automation(commands: list[str]):
    results = []
    async for result in TranslateAndExecute(commands):
        results.append(str(result))
    return results
