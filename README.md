# O.R.A.N.G.E.S.

@ZaidSaudagar

### **Omnipresent Responsive Artificial Neural Guide for Enhanced Systems**

O.R.A.N.G.E.S. is a personal AI-powered desktop assistant designed to streamline daily tasks, automate system interactions, and deliver intelligent responses through an intuitive interface. Built using Python, speech recognition, NLP, and automation libraries, the assistant mimics real-world smart assistants with added customization and offline capabilities.

## 🚀 Features
- **Voice & Text Commands** for hands-free control
- **Real-time Search** across applications and the web
- **System Automation** (open apps, control windows, manage files)
- **NLP-based Chatting** for human-like interactions
- **Custom Modules** for reminders, notes, jokes, and utilities
- **Lightweight UI** with smooth performance

## 🧠 Tech Stack
- **Python 3**
- **SpeechRecognition** for voice commands
- **PyAudio** for microphone I/O
- **NLTK / Transformers** for natural language processing
- **Tkinter / PyQt** for UI (based on chosen version)
- **Automation Libraries:** `pyautogui`, `os`, `subprocess`

## 📁 Project Structure
```
ORANGES/
├── Backend/
│   ├── Automation.py
│   ├── Chatbot.py
│   ├── ImageGeneration.py
│   ├── Model.py
│   ├── RealtimeSearchEngine.py
│   ├── SpeechToText.py
│   └── TextToSpeech.py
│
├── Frontend/
│   ├── Files/
│   │   ├── Database.data
│   │   ├── ImageGeneration.data
│   │   ├── Mic.data
│   │   ├── Responses.data
│   │   └── Status.data
│   ├── Graphics/
│   │   ├── Chats.png
│   │   ├── Close.png
│   │   ├── Jarvis.gif
│   │   ├── Maximize.png
│   │   ├── Mic_off.png
│   │   ├── Mic_on.png
│   │   ├── Minimize.png
│   │   ├── Minimize2.png
│   │   └── Settings.png
│   └── GUI.py
│
├── Data/
│   ├── ChatLog.json
│   ├── speech.mp3
│   └── Voice.html
│
└── myenv/
    └── (Virtual environment files)
```

## ⚙️ How It Works
1. User speaks or types a command
2. Command is processed using NLP
3. System identifies intent (open app, fetch info, automate task, etc.)
4. Assistant executes the command and responds

## 🔐 API Keys Required
ORANGES uses external AI services. You must add your API keys before running the project.

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here
COHERE_API_KEY=your_key_here
```

Make sure to add `.env` to `.gitignore` so your keys are NOT uploaded to GitHub.

## 📦 Installation
```
cd ORANGES
pip install -r requirements.txt
python main.py
```

## 📝 Future Improvements
- Advanced ML-based intent classification
- Browser automation
- Conversation memory
- Plugin system for new modules



---
**O.R.A.N.G.E.S — Your intelligent companion for everyday computing.**

