import cohere  # Import the Cohere library for AI services.
from rich import print  # Import the Rich library to enhance terminal outputs.
from dotenv import dotenv_values  # Import dotenv to load environment variables from a .env file.
import traceback  # For detailed error reporting
from Backend.Chatbot import get_recent_context  # Import conversation context helper

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")

# Retrieve API key.
CohereAPIKey = env_vars.get("CohereAPIKey")

# Check if the API key exists
if not CohereAPIKey:
    raise ValueError("Cohere API key not found. Please check your .env file.")

# Create a Cohere client using the provided API key.
co = cohere.Client(api_key=CohereAPIKey)

# Define a list of recognized function keywords for task categorization.
funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search", "reminder", "run", "screenshot"
]

# Initialize an empty list to store user messages.
# Limit to prevent memory growth (not used for context, just for debugging)
MAX_MESSAGES = 50
messages = []

# Define the preamble that guides the AI model on how to categorize queries.
preamble = """
You are a very accurate Decision-Making Model, which decides what kind of a query is given to you.
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation like 'open facebook, instagram', 'can you write a application and open it in notepad'
*** Do not answer any query, just decide what kind of query is given to you. ***
-> Respond with 'general ( query )' if a query can be answered by a llm model (conversational ai chatbot) and doesn't require any up to date information like if the query is 'who was akbar?' respond with 'general who was akbar?', if the query is 'how can i study more effectively?' respond with 'general how can i study more effectively?', if the query is 'can you help me with this math problem?' respond with 'general can you help me with this math problem?', if the query is 'Thanks, i really liked it.' respond with 'general thanks, i really liked it.' , if the query is 'what is python programming language?' respond with 'general what is python programming language?', etc. Respond with 'general (query)' if a query doesn't have a proper noun or is incomplete like if the query is 'who is he?' respond with 'general who is he?', if the query is 'what's his networth?' respond with 'general what's his networth?', if the query is 'tell me more about him.' respond with 'general tell me more about him.', and so on even if it require up-to-date information to answer. Respond with 'general (query)' if the query is asking about time, day, date, month, year, etc like if the query is 'what's the time?' respond with 'general what's the time?'.
-> Respond with 'realtime ( query )' if a query can not be answered by a llm model (because they don't have realtime data) and requires up to date information like if the query is 'who is indian prime minister' respond with 'realtime who is indian prime minister', if the query is 'tell me about facebook's recent update.' respond with 'realtime tell me about facebook's recent update.', if the query is 'tell me news about coronavirus.' respond with 'realtime tell me news about coronavirus.', etc and if the query is asking about any individual or thing like if the query is 'who is akshay kumar' respond with 'realtime who is akshay kumar', if the query is 'what is today's news?' respond with 'realtime what is today's news?', if the query is 'what is today's headline?' respond with 'realtime what is today's headline?', etc.
-> Respond with 'open (application name or website name)' if a query is asking to open any application like 'open facebook', 'open telegram', etc. but if the query is asking to open multiple applications, respond with 'open 1st application name, open 2nd application name' and so on.
-> Respond with 'close (application name)' if a query is asking to close any application like 'close notepad', 'close facebook', etc. but if the query is asking to close multiple applications or websites, respond with 'close 1st application name, close 2nd application name' and so on.
-> Respond with 'play (song name)' if a query is asking to play any song like 'play afsanay by ys', 'play let her go', etc. but if the query is asking to play multiple songs, respond with 'play 1st song name, play 2nd song name' and so on.
-> Respond with 'generate image (image prompt)' if a query is requesting to generate, create, make, or draw an image with a given prompt. Examples: 'generate image of a lion' respond with 'generate image a lion', 'create an image of a cat in space' respond with 'generate image a cat in space', 'make me a picture of Iron Man' respond with 'generate image Iron Man', 'draw a sunset' respond with 'generate image sunset'. If asking for multiple images, respond with 'generate image 1st prompt, generate image 2nd prompt' and so on.
-> Respond with 'reminder (datetime with message)' if a query is requesting to set a reminder like 'set a reminder at 9:00pm on 25th june for my business meeting.' respond with 'reminder 9:00pm 25th june business meeting'.
-> Respond with 'system (task name)' if a query is asking to mute, unmute, volume up, volume down, shut down, restart, sleep, etc. but if the query is asking to do multiple tasks, respond with 'system 1st task, system 2nd task', etc.
-> Respond with 'content (topic)' if a query is asking to write any type of content like application, codes, emails or anything else about a specific topic but if the query is asking to write multiple types of content, respond with 'content 1st topic, content 2nd topic' and so on.
-> Respond with 'google search (topic)' if a query is asking to search a specific topic on google but if the query is asking to search multiple topics on google, respond with 'google search 1st topic, google search 2nd topic' and so on.
-> Respond with 'youtube search (topic)' if a query is asking to search a specific topic on youtube but if the query is asking to search multiple topics on youtube, respond with 'youtube search 1st topic, youtube search 2nd topic' and so on.
-> Respond with 'run (command)' if a query is asking to execute a terminal or command-line command on the computer, like 'run pip install requests' respond with 'run pip install requests', 'run dir' respond with 'run dir', 'check my python version' respond with 'run python --version', 'list my running processes' respond with 'run tasklist', etc.
-> Respond with 'screenshot (query)' if a query is asking about what is on the screen, to analyze the screen, describe the screen, or take a screenshot. Examples: 'what's on my screen?' respond with 'screenshot what is on my screen', 'describe my screen' respond with 'screenshot describe the screen', 'take a screenshot' respond with 'screenshot capture'.
*** If the query is asking to perform multiple tasks like 'open facebook, telegram and close whatsapp' respond with 'open facebook, open telegram, close whatsapp' ***
*** If the user is saying goodbye or wants to end the conversation like 'bye O.R.A.N.G.E.S.' respond with 'exit'.***
*** Respond with 'general (query)' if you can't decide the kind of query or if a query is asking to perform a task which is not mentioned above. ***
"""

# Define a chat history with predefined user-chatbot interactions for context.
chatHistory = [
    {"role": "User", "message": "how are you?"},
    {"role": "Chatbot", "message": "general how are you?"},
    {"role": "User", "message": "do you like pizza?"},
    {"role": "Chatbot", "message": "general do you like pizza?"},
    {"role": "User", "message": "open chrome and tell me about mahatma gandhi."},
    {"role": "Chatbot", "message": "open chrome, general tell me about mahatma gandhi."},
    {"role": "User", "message": "open chrome and firefox"},
    {"role": "Chatbot", "message": "open chrome, open firefox"},
    {"role": "User", "message": "what is today's date and by the way remind me that i have a dancing performance on 11:00pm 5th aug"},
    {"role": "Chatbot", "message": "general what is today’s date, reminder 11:00pm 5th aug dancing performance"},
    {"role": "User", "message": "chat with me."},
    {"role": "Chatbot", "message": "general chat with me."}
]

# Define the main function for decision-making on queries.
def FirstLayerDMM(prompt: str = "test"):
    try:
        print(f"[DEBUG] FirstLayerDMM called with prompt: {prompt}")
        # Limit messages list size to prevent memory growth
        if len(messages) > MAX_MESSAGES:
            messages[:] = messages[-MAX_MESSAGES:]
        messages.append({"role": "user", "content": f"{prompt}"})

        # Get recent conversation context so the model can resolve references
        recent_context = get_recent_context(n=5)
        context_prefix = ""
        if recent_context:
            context_prefix = f"[Recent conversation for context]\n{recent_context}\n[Current query]\n"
        
        enriched_prompt = context_prefix + prompt
        print(f"[DEBUG] Enriched prompt: {enriched_prompt[:200]}...")

        print("[DEBUG] Calling Cohere API...")
        stream = co.chat_stream(
            model='command-r-08-2024',  # Updated to new model (old command-r deprecated Sept 2025)
            message=enriched_prompt,
            temperature=0.7,
            chat_history=chatHistory,
            prompt_truncation="OFF",
            connectors=[],
            preamble=preamble
        )

        response = ""
        print("[DEBUG] Processing Cohere stream...")

        for event in stream:
            if hasattr(event, "event_type") and event.event_type == "text-generation":
                response += event.text

        print(f"[DEBUG] Raw Cohere response: {response}")

        if not response:
            print("[WARNING] Empty response from Cohere, using fallback")
            return ["general " + prompt]

        response = response.replace("\n", "")
        response = response.split(", ")
        response = [i.strip() for i in response]

        print(f"[DEBUG] Split response: {response}")

        temp = []
        for task in response:
            for func in funcs:
                if task.startswith(func):
                    temp.append(task)
                    break  # Found a match, move to next task

        response = temp
        print(f"[DEBUG] Filtered response: {response}")

        # If no valid function found, default to general query
        if not response:
            print("[WARNING] No valid function found in response, defaulting to general")
            return ["general " + prompt]

        if "(query)" in str(response):
            # Fallback to general query if ambiguous, instead of infinite recursion
            print("[WARNING] Found '(query)' in response, using fallback")
            return ["general " + prompt]
        else:
            print(f"[DEBUG] Returning decision: {response}")
            return response
    except cohere.errors.TooManyRequestsError as e:
        print(f"[ERROR] Cohere API rate limit exceeded (429). Using fallback to general query.")
        print(f"[INFO] This usually means you've hit the API rate limit. Please wait a moment and try again.")
        # Always return something, default to general query
        print(f"[DEBUG] Using fallback: general {prompt}")
        return ["general " + prompt]
    except Exception as e:  # Catch all API errors (CohereAPIError doesn't exist in new library)
        print(f"[ERROR] Cohere API error: {e}")
        traceback.print_exc()
        # Always return something, default to general query
        print(f"[DEBUG] Using fallback: general {prompt}")
        return ["general " + prompt]
    except Exception as e:
        print(f"[ERROR] Error in FirstLayerDMM: {e}")
        traceback.print_exc()
        # Always return something, default to general query
        print(f"[DEBUG] Using fallback: general {prompt}")
        return ["general " + prompt]

if __name__ == "__main__":
    while True:
        try:
            user_input = input("> ")
            print(FirstLayerDMM(user_input))
        except KeyboardInterrupt:
            print("\n[red]Exiting...[/red]")
            break
        except Exception as e:
            print(f"[red]Error:[/red] {e}")
