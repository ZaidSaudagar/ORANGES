# Main.py

from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus,
    SetSpeakButtonStatus,
    GetTextInput )
from Config import TempDirectoryPath, DataDirectoryPath
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealTimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.HybridChat import HybridChatBot

from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os
import traceback
import atexit  # For cleanup on exit
from Backend.ClipboardMonitor import clipboard_monitor_loop

env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
DefaultMessage = f'''{Username}: Hello {Assistantname}, How are you Sir ?
{Assistantname} : Welcome {Username}. I am doing well, Sir. How may i help you today ???'''
subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search", "run", "screenshot", "exit"]

# Cleanup function for proper resource management
def cleanup_resources():
    """Clean up all resources on application exit"""
    try:
        print("[DEBUG] Cleaning up resources...")
        
        # Terminate all subprocesses
        for process in subprocesses:
            try:
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Force kill if it doesn't terminate
                        process.kill()
                        process.wait(timeout=2)
            except Exception as e:
                print(f"[ERROR] Error terminating subprocess: {e}")
        
        # Cleanup WebDriver from SpeechToText
        try:
            from Backend.SpeechToText import cleanup_driver
            cleanup_driver()
        except Exception as e:
            print(f"[ERROR] Error cleaning up WebDriver: {e}")
            
        print("[DEBUG] Cleanup completed")
    except Exception as e:
        print(f"[ERROR] Error during cleanup: {e}")

# Register cleanup function
atexit.register(cleanup_resources)

def ShowDefaultChatIfNoChats():
    try:
        with open(DataDirectoryPath('ChatLog.json'), 'r', encoding='utf-8') as file:
            content = file.read()
            if len(content) == 0:
                with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as db_file:
                    db_file.write("")
                
                with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as resp_file:
                    resp_file.write(DefaultMessage)
    except FileNotFoundError:
        # Create empty ChatLog.json if it doesn't exist
        with open(DataDirectoryPath('ChatLog.json'), 'w', encoding='utf-8') as file:
            json.dump([], file)
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as db_file:
            db_file.write("")
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as resp_file:
            resp_file.write(DefaultMessage)
    except Exception as e:
        print(f"[ERROR] Error in ShowDefaultChatIfNoChats: {e}")
        traceback.print_exc()

def ReadChatLogJson():
    with open(DataDirectoryPath('ChatLog.json'), 'r', encoding='utf-8') as file:
        chatlog_data = json.load(file)
    return chatlog_data

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant: {entry['content']}\n"
    formatted_chatlog = formatted_chatlog.replace("User", Username + " ")
    formatted_chatlog = formatted_chatlog.replace("Assistant", Assistantname + " ")
    
    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    """Load and display chat history - preserves existing chats"""
    try:
        with open(TempDirectoryPath('Database.data'), "r", encoding='utf-8') as File:
            Data = File.read()
        if len(str(Data)) > 0:
            # Only update if there's actual content
            with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as File:
                File.write(Data)
    except Exception as e:
        print(f"[DEBUG] Error in ShowChatsOnGUI: {e}")

def InitialExecution():
    # Initialize mic status - default to UNMUTED (mic on) visually
    # But listening only happens when speak button is pressed
    try:
        current_mic = GetMicrophoneStatus().strip()
        if not current_mic or current_mic == "":
            SetMicrophoneStatus("True")  # Default to unmuted visually
    except:
        SetMicrophoneStatus("True")  # Default to unmuted
    
    # Initialize speak button to False (not pressed)
    SetSpeakButtonStatus("False")
    
    # Don't clear chat history - preserve existing chats
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

InitialExecution()

def MainExecution(Query=None):
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    def check_stop():
        try:
            with open(TempDirectoryPath('Stop.data'), "r", encoding='utf-8') as file:
                if file.read().strip() == "True":
                    with open(TempDirectoryPath('Stop.data'), "w", encoding='utf-8') as file:
                        file.write("False")
                    return True
        except:
            pass
        return False

    try:
        if check_stop(): return
        
        # If Query wasn't passed (legacy or direct call), listen now
        if Query is None:
            SetAssistantStatus("Listening ... ")
            Query = SpeechRecognition()
        
        if not Query:
            SetAssistantStatus("Available ...")
            return
            
        if check_stop(): return
        
        print(f"[DEBUG] Query received: {Query}")
        
        # Show user's query - ShowTextToScreen will append automatically
        # (Note: Query is already shown in FirstThread, but showing here ensures it's displayed)
        new_message = f"{Username} : {Query}"
        ShowTextToScreen(new_message)
        SetAssistantStatus("Thinking ... ")
        
        if check_stop(): return
        
        try:
            Decision = FirstLayerDMM(Query)
        except Exception as e:
            print(f"[ERROR] Error in decision making: {e}")
            traceback.print_exc()
            # Fallback to general query if decision making fails
            Decision = ["general " + Query]
        
        print("")
        print(f"[DEBUG] Decision : {Decision}")
        print("")

        # Ensure Decision is not empty - if it is, default to general query
        if not Decision or len(Decision) == 0:
            print("[WARNING] Empty decision, defaulting to general query")
            Decision = ["general " + Query]

        G = any([i for i in Decision if i.startswith("general")])
        R = any([i for i in Decision if i.startswith("realtime")])
        Merged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
        )

        for queries in Decision:
            if "generate " in queries:
                ImageGenerationQuery = str(queries)
                ImageExecution = True
                print(f"[DEBUG] Image generation detected! Query: {ImageGenerationQuery}")

        for queries in Decision:
            if TaskExecution == False:
                if any(queries.startswith(func) for func in Functions):
                    if "exit" in queries:
                        QueryFinal = "Okay, Bye!"
                        try:
                            Answer, model_label = HybridChatBot(QueryModifier(QueryFinal))
                            ShowTextToScreen(f"{Assistantname} ({model_label}) : {Answer}")
                            SetAssistantStatus("Answering ...")
                            TextToSpeech(Answer)
                        except Exception as e:
                            print(f"[ERROR] Error in exit sequence: {e}")
                            traceback.print_exc()
                        os._exit(1)
                    else:
                        try:
                            # Run automation and get feedback
                            Results = run(Automation(list(Decision)))
                            if Results:
                                for res in Results:
                                    if res:
                                        print(f"[DEBUG] Automation Result: {res}")
                                        ShowTextToScreen(f"{Assistantname} : {res}")
                                        # Speak the result for confirmation
                                        SetAssistantStatus("Answering ...")
                                        TextToSpeech(res)
                                        SetAssistantStatus("Available ...")
                                        
                        except Exception as e:
                            print(f"[ERROR] Error in Automation: {e}")
                            traceback.print_exc()
                            SetAssistantStatus("Error occurred...")
                            ShowTextToScreen(f"{Assistantname}: Sorry, an error occurred during automation.")
                    TaskExecution = True

        if ImageExecution == True:
            try:
                print(f"[DEBUG] Starting image generation subprocess...")
                SetAssistantStatus("Generating images ...")
                ShowTextToScreen(f"{Assistantname}: Generating images for you, please wait...")
                
                with open(TempDirectoryPath('ImageGeneration.data'), "w", encoding='utf-8') as file:
                    file.write(f"{ImageGenerationQuery},True")
                
                # Run from project root directory so imports work
                project_root = os.path.dirname(os.path.abspath(__file__))
                p1 = subprocess.Popen(
                    ['python', os.path.join('Backend', 'ImageGeneration.py')],
                    cwd=project_root,  # Set working directory to project root
                    shell=False
                )
                subprocesses.append(p1)
                print(f"[DEBUG] ImageGeneration.py started with PID: {p1.pid}")
            except Exception as e:
                print(f"[ERROR] Error starting ImageGeneration.py: {e}")
                traceback.print_exc()
                SetAssistantStatus("Error occurred...")
                ShowTextToScreen(f"{Assistantname}: Sorry, an error occurred while starting image generation.")

        if G and R or R:
            print("[DEBUG] Processing realtime search...")
            SetAssistantStatus("Searching ...")
            try:
                if check_stop(): return
                Answer = RealTimeSearchEngine(QueryModifier(Merged_query))
                print(f"[DEBUG] RealTimeSearchEngine returned: {Answer[:100]}...")
                if check_stop(): return
                ShowTextToScreen(f"{Assistantname}: {Answer}")
                SetAssistantStatus("Answering ...")
                try:
                    print(f"[DEBUG] MainExecution: Calling TextToSpeech for answer (RT)...")
                    TextToSpeech(Answer)
                    print("[DEBUG] TextToSpeech call finished")
                    SetAssistantStatus("Available ...")  # Ready for next conversation
                except Exception as e:
                    print(f"[ERROR] Error in TextToSpeech call: {e}")
                    traceback.print_exc()
                    SetAssistantStatus("Available ...")  # Reset even on error
            except Exception as e:
                print(f"[ERROR] Error in RealTimeSearchEngine: {e}")
                traceback.print_exc()
                SetAssistantStatus("Error occurred...")
                ShowTextToScreen(f"{Assistantname}: Sorry, an error occurred while searching. Please try again.")
            return True

        for queries in Decision:
            if "general" in queries:
                print("[DEBUG] Processing general query...")
                SetAssistantStatus("Thinking ...")
                QueryFinal = queries.replace("general ", "")
                try:
                    if check_stop(): return
                    Answer, model_label = HybridChatBot(QueryModifier(QueryFinal))
                    print(f"[DEBUG] {model_label} returned: {Answer[:100]}...")
                    if check_stop(): return
                    ShowTextToScreen(f"{Assistantname} ({model_label}) : {Answer}")
                    SetAssistantStatus("Answering ...")
                    try:
                        print(f"[DEBUG] MainExecution: Calling TextToSpeech for answer ({model_label})...")
                        TextToSpeech(Answer)
                        print("[DEBUG] TextToSpeech call finished")
                        SetAssistantStatus("Available ...")  # Ready for next conversation
                    except Exception as e:
                        print(f"[ERROR] Error in TextToSpeech call: {e}")
                        traceback.print_exc()
                        SetAssistantStatus("Available ...")  # Reset even on error
                except Exception as e:
                    print(f"[ERROR] Error in ChatBot: {e}")
                    traceback.print_exc()
                    SetAssistantStatus("Error occurred...")
                    ShowTextToScreen(f"{Assistantname}: Sorry, an error occurred. Please try again.")
                return True

            elif "realtime" in queries:
                print("[DEBUG] Processing realtime query...")
                SetAssistantStatus("Searching ...")
                QueryFinal = queries.replace("realtime ", "")
                try:
                    Answer = RealTimeSearchEngine(QueryModifier(QueryFinal))
                    print(f"[DEBUG] RealTimeSearchEngine returned: {Answer[:100]}...")
                    ShowTextToScreen(f"{Assistantname} : {Answer}")
                    SetAssistantStatus("Answering ...")
                    try:
                        TextToSpeech(Answer)
                        print("[DEBUG] TextToSpeech completed")
                        SetAssistantStatus("Available ...")  # Ready for next conversation
                    except Exception as e:
                        print(f"[ERROR] Error in TextToSpeech: {e}")
                        traceback.print_exc()
                        SetAssistantStatus("Available ...")  # Reset even on error
                except Exception as e:
                    print(f"[ERROR] Error in RealTimeSearchEngine: {e}")
                    traceback.print_exc()
                    SetAssistantStatus("Error occurred...")
                    ShowTextToScreen(f"{Assistantname}: Sorry, an error occurred while searching. Please try again.")
                return True
        
        print("[DEBUG] No matching query type found, returning...")
        SetAssistantStatus("Available ...")
    except Exception as e:
        print(f"[ERROR] Critical error in MainExecution: {e}")
        traceback.print_exc()
        SetAssistantStatus("Error occurred...")
        ShowTextToScreen(f"{Assistantname}: A critical error occurred. Please check console for details.")

# Constants for timing
DEBOUNCE_TIME = 3.0  # seconds
THREAD_SLEEP_IDLE = 0.08  # seconds
THREAD_SLEEP_AFTER_PROCESSING = 1.0  # seconds
THREAD_SLEEP_ERROR = 0.8  # seconds

def FirstThread():
    from time import time
    last_query = ""
    last_query_time = 0
    
    while True:
        try:
            # Check stop flag
            try:
                with open(TempDirectoryPath('Stop.data'), "r", encoding='utf-8') as file:
                    if file.read().strip() == "True":
                        # Clear stop flag and reset status after brief delay
                        with open(TempDirectoryPath('Stop.data'), "w", encoding='utf-8') as file:
                            file.write("False")
                        # Status is already "Stopped..." from SetStopFlag
                        # Wait briefly so user sees it, then transition to Available
                        sleep(0.5)
                        SetAssistantStatus("Available ...")
                        sleep(THREAD_SLEEP_IDLE)
                        continue
            except FileNotFoundError:
                # Create file if it doesn't exist
                with open(TempDirectoryPath('Stop.data'), "w", encoding='utf-8') as file:
                    file.write("False")
            except Exception as e:
                print(f"[DEBUG] Error reading Stop.data: {e}")
            
            # Check speak button or mic status
            try:
                with open(TempDirectoryPath('Speak.data'), "r", encoding='utf-8') as file:
                    speak_status = file.read().strip() == "True"
            except FileNotFoundError:
                # Create file if it doesn't exist
                with open(TempDirectoryPath('Speak.data'), "w", encoding='utf-8') as file:
                    file.write("False")
                speak_status = False
            except Exception as e:
                print(f"[DEBUG] Error reading Speak.data: {e}")
                speak_status = False
            
            CurrentStatus = GetMicrophoneStatus()
            
            # Prevent duplication and listening while AI is talking
            AIStatus = GetAssistantStatus()
            if "Answering" in AIStatus or "Speaking" in AIStatus:
                sleep(0.5)
                continue

            # Check for text input first (alternative to speech)
            text_query = GetTextInput()
            if text_query:
                try:
                    print(f"[DEBUG] Text input received: {text_query}")
                    SetAssistantStatus("Processing ...")
                    
                    current_time = time()
                    # Show query on screen immediately
                    new_message = f"{Username} : {text_query}"
                    ShowTextToScreen(new_message)
                    MainExecution(text_query)
                    sleep(THREAD_SLEEP_AFTER_PROCESSING)
                    continue
                except Exception as e:
                    print(f"[ERROR] Error processing text input: {e}")
                    traceback.print_exc()
                    SetAssistantStatus("Available ...")

            # Check if speak button was pressed (push-to-talk)
            if speak_status:
                try:
                    # Show listening status before blocking on SpeechRecognition
                    SetAssistantStatus("Listening ... ")
                    
                    # Get query directly to allow debouncing
                    Query = SpeechRecognition()
                    
                    # ALWAYS reset speak button after recognition attempt (whether successful or not)
                    # This is what makes it push-to-talk - auto-resets after recognition
                    SetSpeakButtonStatus("False")
                    # DON'T change mic status - mic button controls that separately!
                    
                    if Query and Query.strip():
                        current_time = time()
                        # Debounce: Ignore if same query within DEBOUNCE_TIME seconds
                        if Query == last_query and (current_time - last_query_time < DEBOUNCE_TIME):
                            print(f"[DEBUG] Ignored duplicate query (Debounce): {Query}")
                        else:
                            last_query = Query
                            last_query_time = current_time
                            # Show query on screen immediately
                            new_message = f"{Username} : {Query}"
                            ShowTextToScreen(new_message)
                            MainExecution(Query)
                            # Give system room to breathe after processing
                            sleep(THREAD_SLEEP_AFTER_PROCESSING)
                    else:
                        # Empty query - just reset status
                        print("[DEBUG] Empty query received, resetting status")
                        SetAssistantStatus("Available ...")
                except Exception as e:
                    print(f"[ERROR] Error in MainExecution call: {e}")
                    traceback.print_exc()
                    # Ensure button is reset even on error
                    SetSpeakButtonStatus("False")
                    # DON'T change mic status - mic button controls that separately!
                    SetAssistantStatus("Available ...")
            
            # REMOVED: Continuous listening mode
            # Only speak button triggers listening - mic button is just visual
            else:
                AIStatus = GetAssistantStatus()
                
                if "Available ..." in AIStatus:
                    sleep(THREAD_SLEEP_IDLE)
                else:
                    SetAssistantStatus("Available ...")
        except Exception as e:
            print(f"[ERROR] Critical error in FirstThread: {e}")
            traceback.print_exc()
            SetAssistantStatus("Error occurred...")
            sleep(THREAD_SLEEP_ERROR)

def SecondThread():
    GraphicalUserInterface()

def ResetSystemFlags():
    """Reset all system flags to default state on startup"""
    try:
        # Reset Stop flag
        with open(TempDirectoryPath('Stop.data'), "w", encoding='utf-8') as file:
            file.write("False")
        
        # Reset Status
        SetAssistantStatus("Available ...")
        
        # Reset Speak Button (Not listening)
        SetSpeakButtonStatus("False")
        
        # Reset Mic (Default to False/Off for safety, or True if preferred)
        # Let's default to True (Ready) as per usual assistant behavior
        SetMicrophoneStatus("True")
        
        # Clear Text Input
        with open(TempDirectoryPath('TextInput.data'), "w", encoding='utf-8') as file:
            file.write("")
            
        print("[DEBUG] System flags reset to default")
    except Exception as e:
        print(f"[ERROR] Error resetting system flags: {e}")

if __name__ == "__main__":
    try:
        # Main Execution
        ResetSystemFlags()
        
        thread2 = threading.Thread(target=FirstThread, daemon=True)
        thread2.start()
        
        # Start clipboard monitor
        clipboard_thread = threading.Thread(target=clipboard_monitor_loop, daemon=True)
        clipboard_thread.start()
        
        SecondThread()

    except KeyboardInterrupt:
        print("\n[DEBUG] Application interrupted by user")
    except Exception as e:
        print(f"[ERROR] Critical error in main: {e}")
        traceback.print_exc()
    finally:
        cleanup_resources()
