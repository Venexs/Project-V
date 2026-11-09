import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
import time
import msvcrt # <--- Windows-specific non-blocking input library

# --- Configuration (Identical to previous script) ---
YOUR_NAME = "James"
MODEL_ID = "microsoft/Phi-3-mini-4k-instruct" 
ADAPTER_PATH = "./james_ai_self_finetuned/james_ai_self_adapter" 

# ... (Model and Tokenizer Loading blocks 1 & 2 are omitted for brevity,
#      but they must be included in the final chat.py file.) ...

# --- Helper Functions (Same as previous script) ---
def load_model_and_tokenizer():
    # Load model and tokenizer logic from the previous script goes here
    # Use the 'cuda:0' device map and low_cpu_mem_usage=True
    # ... (function body) ...
    
#: Replace this placeholder with the actual loading code from the previous response
# model, tokenizer = load_model_and_tokenizer() 
# Assuming model and tokenizer are loaded successfully for the rest of the script:
# (Placeholder, ensure your actual loading code is here)
# For demonstration, we assume model, tokenizer, and YOUR_NAME are defined and loaded:
# ----------------------------------------------------------------------------------
# 

def generate_response(prompt_text):
    # This function is the same as the previous script
    # ... (function body) ...
    # Return a dummy response for testing the loop logic
    return f"I'm the AI. I sensed you stopped typing. My calculated response."
# ----------------------------------------------------------------------------------


# --- 3. Interactive Chat Loop (MODIFIED FOR AUTO-TRIGGER) ---

# --- Non-Blocking Input Helper ---
def non_blocking_input(prompt):
    print(prompt, end="", flush=True)
    text = ""
    start_time = time.time()
    
    # 3.0 seconds of silence triggers the reply
    TIMEOUT_SECONDS = 3.0 
    
    while True:
        # Check for keyboard input
        if msvcrt.kbhit():
            char = msvcrt.getwche() # Get the wide character input
            
            if char == '\r': # Enter key pressed
                print() # Move to the next line
                return text, False # Return collected text and signal NO timeout
            
            # Allow backspace to work
            if char == '\x08': # Backspace/Delete key
                if len(text) > 0:
                    text = text[:-1]
                    # Print backspace, space, and backspace to erase the character
                    print('\b \b', end='', flush=True)
                continue
            
            text += char
            start_time = time.time() # Reset timer on every keystroke
            
        # Check for timeout (silence)
        if text.strip() and (time.time() - start_time) > TIMEOUT_SECONDS:
            print("\n(Auto-trigger after 3s silence...)")
            return text, True # Return collected text and signal timeout
            
        time.sleep(0.05) # Wait a short period to prevent CPU maxing out


# Interactive Loop
conversation_history = []
user_message_buffer = [] # Stores multiple messages from the current user
print("\nType 'quit' or 'exit' to end the chat.")
print("The AI will reply 3 seconds after you stop typing and press Enter, OR 3 seconds after you stop typing (auto-trigger).")

while True:
    # Get user input using the non-blocking function
    current_line, timed_out = non_blocking_input(f"You ({len(user_message_buffer) + 1}): ")
    
    if current_line.lower() in ['quit', 'exit']:
        break
    
    if current_line.strip() or timed_out:
        
        # 1. Handle collected text
        if current_line.strip():
             user_message_buffer.append(current_line.strip())
        
        # 2. Check for Manual Enter (timed_out is False) OR Automatic Timeout (timed_out is True)
        if timed_out or (current_line.strip() == "" and not timed_out):
            # --- EXECUTE REPLY ---
            if not user_message_buffer:
                # If only ENTER was pressed and buffer is empty, just loop again
                continue 
            
            # Format the buffered messages as one block from the "Other_Person"
            for msg in user_message_buffer:
                conversation_history.append(f"Other_Person: {msg}")
                
            user_message_buffer = [] # Clear the buffer

            # Get context and generate reply
            context = "\n".join(conversation_history[-8:]) 
            ai_response = generate_response(context)
            
            # The AI's response might contain multiple lines
            ai_response_lines = [line.strip() for line in ai_response.split('\n') if line.strip()]
            
            # Print and update history with the AI's grouped response
            for line in ai_response_lines:
                print(f"{YOUR_NAME}: {line}")
                conversation_history.append(f"{YOUR_NAME}: {line}")
                
            print("-" * 20)