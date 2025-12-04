from AppOpener import open, close as appopen
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

messages = []

# ✅ Format system message using environment variable safely
SystemChatBot = [{
    "role": "system",
    "content": f"Hello, I am {env_vars.get('Username', 'User')}. You're a content writer. You have to write content like letters, codes, applications, essays, notes, songs, poems etc."
}]

def GoogleSearch(Topic):
    search(Topic)
    return True

def Content(Topic):
    def OpenNotepad(file):
        subprocess.Popen(['notepad.exe', file])

    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
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

        Answer = Answer.replace("</s*>", "")
        messages.append({"role": "assistant", "content": Answer})
        return Answer

    Topic = Topic.replace("Content ", "")
    ContentByAI = ContentWriterAI(Topic)

    filepath = rf"Data\{Topic.lower().replace(' ', '')}.txt"
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(ContentByAI)

    OpenNotepad(filepath)
    return True

def YouTubeSearch(Topic):
    url = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(url)
    return True

def PlayYoutube(query):
    playonyt(query)
    return True

def OpenApp(app, sess=requests.session()):
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        def extract_links(html):
            if html is None:
                return []
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', {'jsname': 'UWckNb'})
            return [link.get('href') for link in links if link.get('href')]

        def search_google(query):
            url = f"https://www.google.com/search?q={query}"
            headers = {"User-Agent": user_agent}
            response = sess.get(url, headers=headers)
            if response.status_code == 200:
                return response.text
            else:
                print("Apologies Sir, I've Failed to retrieve search results.")
                return None

        html = search_google(app)
        links = extract_links(html)
        if links:
            webbrowser.open(links[0])
        return True

def CloseApp(app):
    if "chrome" in app:
        return True  # Skip Chrome
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        return False

def System(command):
    def mute(): keyboard.press_and_release("volume mute")
    def unmute(): keyboard.press_and_release("volume unmute")
    def volume_up(): keyboard.press_and_release("volume up")
    def volume_down(): keyboard.press_and_release("volume down")

    commands_map = {
        "mute": mute,
        "unmute": unmute,
        "volume up": volume_up,
        "volume down": volume_down
    }

    func = commands_map.get(command)
    if func:
        func()
        return True
    return False

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
        else:
            print(f"[red]No Function Found for: {command}[/red]")

    results = await asyncio.gather(*funcs)
    for result in results:
        yield result

async def Automation(commands: list[str]):
    async for result in TranslateAndExecute(commands):
        pass
    return True
