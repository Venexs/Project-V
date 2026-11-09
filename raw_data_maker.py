import re
import json
import os
import pandas as pd

# --- Configuration ---
FILE_NAME = "Whatsapp Data/WhatsApp Chat with Aisha Bangladesh/WhatsApp Chat with Aisha Bangladesh.txt"
OUTPUT_FILE = "Json Data/james_fine_tuning_data_with_aisha_bangladesh.jsonl"
YOUR_NAME = "James" 

# --- Regex Pattern ---
# This pattern is common for WhatsApp exports. It captures the date, time, user name, and message.
# Adjust this slightly if your specific export format is different!
# Example: [7/8/24, 11:52 PM] James: You're insane 
# The pattern below handles the common format: Date/Time - Name: Message
# Note: WhatsApp often uses brackets around the date/time in the export, which is common.
# I'll use a slightly broader pattern that should catch the common variations.
# Pattern: (\d{1,2}\/\d{1,2}\/\d{2,4}, \d{1,2}:\d{2}\s?(?:AM|PM)?) - ([^:]+): (.*)
# Based on your previous example, a simpler pattern:
pattern = r"(\d{1,2}\/\d{1,2}\/\d{2}, \d{1,2}:\d{2}\s?(?:AM|PM|am|pm)?) - ([^:]+): (.*)"


# --- 1. Reading and Parsing the File ---
print(f"1. Reading and parsing {FILE_NAME}...")
parsed_data = []
try:
    with open(FILE_NAME, 'r', encoding='utf-8') as f:
        for line in f:
            # WhatsApp lines sometimes start with a blank line or system messages, skip those
            if line.strip() == "":
                continue

            match = re.search(pattern, line.strip())
            if match:
                # Groups: 1=Timestamp, 2=User, 3=Message
                timestamp, user, message = match.groups()
                parsed_data.append({
                    'timestamp': timestamp.strip(),
                    'user': user.strip(),
                    'message': message.strip()
                })
            # else:
            #     # Optional: print lines that didn't match the pattern for debugging
            #     print(f"Skipped line (no match): {line.strip()}") 
except FileNotFoundError:
    print(f"ERROR: File not found at '{FILE_NAME}'. Please check the path.")
    exit()

if not parsed_data:
    print("ERROR: No valid chat messages were parsed. Check the regex pattern against your file's format.")
    exit()

df = pd.DataFrame(parsed_data)


# --- 2. Filtering and Context-Building (Creating Prompt-Completion Pairs) ---
print("2. Building conversational context pairs...")
dataset = []
current_prompt = [] # Messages from Carl/Others (the context for James's response)

# The logic here assumes: A response from James is triggered by the preceding messages.
for index, row in df.iterrows():
    if row['user'] != YOUR_NAME:
        # If it's not you, add it to the prompt history
        current_prompt.append(f"{row['user']}: {row['message']}")
    else:
        # If it IS you (James), this is the Completion/Answer
        prompt_text = "\n".join(current_prompt)
        completion_text = row['message']

        if current_prompt:
            dataset.append({
                'prompt': prompt_text,
                'completion': completion_text
            })

        # Reset for the next turn. The James message just sent becomes part of the *new* context.
        current_prompt = [f"{YOUR_NAME}: {completion_text}"] 
        
        # If James sends multiple messages in a row, they are treated as a single block
        # in the 'completion' of the previous turn, but here they are separated.
        # This implementation simplifies to one response per prompt.
        # You may need to refine the logic to group consecutive messages from James.


# --- 3. Formatting for Fine-Tuning (JSONL) ---
print(f"3. Formatting {len(dataset)} pairs into JSONL...")
final_data = []

for item in dataset:
    # Use a clear instruction format for the SFT Trainer
    instruction = (
        f"You are {YOUR_NAME}. Given the conversation history, provide {YOUR_NAME}'s next response."
    )
    
    # The standard Llama/Mistral instruction template format:
    formatted_text = (
        f"<s>[INST] {instruction}\n\n"
        f"Conversation History:\n{item['prompt']}\n\n"
        f"Your Response:[/INST] {item['completion']}</s>"
    )
    
    final_data.append({
        'text': formatted_text
    })

# Write the data to the final fine-tuning file
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for entry in final_data:
        f.write(json.dumps(entry) + '\n')

print(f"\n✅ Success! Fine-tuning data saved to {OUTPUT_FILE}")
print(f"Total conversational pairs created: {len(final_data)}")