"""
Conversation Training System for Vashrak AI
Allows users to chat with the AI and rate responses for fine-tuning data collection
"""
import sys
import json
import time
import os
from typing import Optional, Tuple
import re

# Import modules
from modules.identity import load_identity, get_name
from modules.llm import generate_response, generate_internal_thought
from modules.consciousness import get_consciousness, process_with_consciousness
from modules.memory import associative_recall, create_memory
from modules.knowledge import retrieve_knowledge
from modules.rewards import record_reward
from modules.emotions import create_emotion_graph

# Training data storage
TRAINING_DATA_FILE = "training_conversations.jsonl"
TRAINING_RATINGS_FILE = "training_ratings.jsonl"

def load_identity_data():
    """Load identity for the AI"""
    identity = load_identity()
    return identity

def store_training_conversation(user_input: str, ai_response: str, rating: int,
                                 context_memories=None, context_knowledge=None):
    """Store conversation with rating for later training"""

    # Save to ratings file (structured with metadata)
    rating_entry = {
        "timestamp": time.time(),
        "user_input": user_input,
        "ai_response": ai_response,
        "rating": rating,
        "memory_count": len(context_memories) if context_memories else 0,
        "knowledge_count": len(context_knowledge) if context_knowledge else 0
    }

    with open(TRAINING_RATINGS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rating_entry) + '\n')

    # Save to JSONL training format (similar to existing fine-tuning data)
    # Format compatible with training.py
    formatted_text = (
        f"<s>[INST] You are Vashrak, an autonomous AI companion. "
        f"Given a user input, respond in a casual, concise manner.\n\n"
        f"User Input: {user_input}\n\n"
        f"Your Response:[/INST] {ai_response}</s>"
    )

    training_entry = {
        "text": formatted_text,
        "rating": rating,
        "user_input": user_input,
        "ai_response": ai_response
    }

    with open(TRAINING_DATA_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(training_entry) + '\n')

    print(f"[Training] Conversation rated {rating}/10 and saved")

def get_user_rating(ai_response: str) -> int:
    """Get user rating for AI response"""
    while True:
        try:
            rating_input = input("\n[Rating] Rate this response from 1-10 (or 'skip' to skip): ").strip()

            if rating_input.lower() in ['skip', 's', '']:
                print("[Training] Rating skipped")
                return 0

            rating = int(rating_input)
            if 1 <= rating <= 10:
                return rating
            else:
                print("Please enter a number between 1 and 10")
        except ValueError:
            print("Please enter a valid number or 'skip'")
        except KeyboardInterrupt:
            print("\n[Training] Interrupted")
            return 0

class VashrakTrainingAI:
    """Training version of Vashrak AI with rating collection"""

    def __init__(self):
        self.identity = load_identity_data()
        self.name = get_name()
        self.consciousness = get_consciousness()
        self.consciousness.think("I am in training mode. Learning from feedback.", "observation")

        print(f"[{self.name}] Training Mode Initialized")
        print(f"[{self.name}] Have a conversation and rate each response 1-10")
        print(f"[System] Say 'quit' or 'exit' to end training session\n")

        # Training stats
        self.conversation_count = 0
        self.total_rating = 0
        self.rated_count = 0

    def process_interaction(self, user_input: str) -> str:
        """Process user input and generate response"""
        try:
            # Process through consciousness
            process_with_consciousness(user_input, {})
            self.consciousness.think(f"Training input: {user_input[:50]}", "observation")

            # Retrieve context
            try:
                memory_results = associative_recall(user_input, top_k=3)
                if not isinstance(memory_results, list):
                    memory_results = []
            except:
                memory_results = []

            try:
                knowledge_results = retrieve_knowledge(user_input, top_k=3)
                if not isinstance(knowledge_results, list):
                    knowledge_results = []
            except:
                knowledge_results = []

            # Filter relevance
            memory_results = [(mid, s) for mid, s in memory_results if isinstance(s, (int, float)) and s >= 0.15]
            knowledge_results = [(kid, s) for kid, s in knowledge_results if isinstance(s, (int, float)) and s >= 0.15]

            # Generate response
            response = generate_response(
                user_input,
                context_memories=memory_results,
                context_knowledge=knowledge_results,
                identity=self.identity
            )

            if not response:
                response = "Not sure about that."

            # Consciousness reflects
            self.consciousness.think(f"I responded: {response[:50]}", "observation")

            return response, memory_results, knowledge_results

        except Exception as e:
            print(f"[Error] {e}")
            return "Sorry, I encountered an error", [], []

    def run_training_session(self):
        """Main training conversation loop"""
        print(f"\n[{self.name}] Ready for training conversation\n")

        while True:
            try:
                # Get user input
                user_input = input(f"[User] ").strip()

                if not user_input:
                    continue

                # Check for exit
                if user_input.lower() in ['quit', 'exit', 'q', 'goodbye']:
                    print(f"\n[{self.name}] Ending training session")
                    self.print_training_stats()
                    break

                # Process and respond
                print(f"\n[Processing] Thinking...")
                response, memories, knowledge = self.process_interaction(user_input)

                print(f"[{self.name}] {response}\n")

                # Get rating
                rating = get_user_rating(response)

                if rating > 0:
                    self.conversation_count += 1
                    self.total_rating += rating
                    self.rated_count += 1

                    # Store conversation
                    store_training_conversation(user_input, response, rating, memories, knowledge)

                    # Record reward
                    record_reward(user_input, response, (rating - 5.5) / 4.5, feedback_type="explicit")

                    print(f"[Training] Avg rating: {self.total_rating / self.rated_count:.2f}/10 ({self.rated_count} rated)")
                else:
                    print("[Training] No rating recorded")

            except KeyboardInterrupt:
                print(f"\n\n[{self.name}] Training interrupted")
                self.print_training_stats()
                break
            except Exception as e:
                print(f"[Error] {e}")
                import traceback
                traceback.print_exc()

    def print_training_stats(self):
        """Print training session statistics"""
        print("\n" + "="*50)
        print("Training Session Summary")
        print("="*50)
        print(f"Total conversations: {self.conversation_count}")
        if self.rated_count > 0:
            print(f"Average rating: {self.total_rating / self.rated_count:.2f}/10")
        print(f"Data saved to: {TRAINING_DATA_FILE}")
        print(f"Ratings saved to: {TRAINING_RATINGS_FILE}")
        print("="*50 + "\n")

        # Show how to use the data
        print("[Training] To use this data for fine-tuning:")
        print("1. The conversation data is saved in JSONL format")
        print("2. Merge it with your existing Json Data/ files")
        print("3. Run training.py with the merged data")
        print(f"4. Filter by rating > 7 for high-quality examples")
        print()

def filter_training_data_by_rating(min_rating: int = 7):
    """Filter training data by minimum rating"""
    if not os.path.exists(TRAINING_DATA_FILE):
        print("No training data found")
        return

    filtered_data = []
    with open(TRAINING_DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            if entry.get('rating', 0) >= min_rating:
                filtered_data.append(entry)

    # Write filtered file
    filtered_file = f"training_conversations_rating_{min_rating}+.jsonl"
    with open(filtered_file, 'w', encoding='utf-8') as f:
        for entry in filtered_data:
            f.write(json.dumps(entry) + '\n')

    print(f"Filtered {len(filtered_data)} conversations with rating >= {min_rating}")
    print(f"Saved to: {filtered_file}")
    return filtered_file

def merge_with_existing_json_data():
    """Merge training conversations with existing Json Data folder"""
    import glob

    if not os.path.exists(TRAINING_DATA_FILE):
        print("No training data found")
        return

    # Collect existing data
    existing_files = glob.glob("Json Data/*.jsonl")
    all_conversations = []

    for file in existing_files:
        print(f"Loading {file}...")
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line)
                all_conversations.append(entry)

    # Load training data
    print(f"Loading {TRAINING_DATA_FILE}...")
    with open(TRAINING_DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            # Convert to existing format if needed
            if 'text' in entry:
                all_conversations.append(entry)

    # Save merged data
    merged_file = "Json Data/merged_training_with_conversations.jsonl"
    with open(merged_file, 'w', encoding='utf-8') as f:
        for entry in all_conversations:
            f.write(json.dumps(entry) + '\n')

    print(f"Merged {len(all_conversations)} total conversations")
    print(f"Saved to: {merged_file}")

if __name__ == "__main__":
    print("="*60)
    print("Vashrak AI - Conversation Training System")
    print("="*60)
    print("\nOptions:")
    print("1. Start training session (chat and rate responses)")
    print("2. Filter existing training data by rating")
    print("3. Merge training data with existing Json Data")
    print("4. Exit")

    choice = input("\nChoose option (1-4): ").strip()

    if choice == '1':
        ai = VashrakTrainingAI()
        ai.run_training_session()
    elif choice == '2':
        try:
            min_rating = int(input("Minimum rating (1-10): "))
            filter_training_data_by_rating(min_rating)
        except ValueError:
            print("Invalid rating")
    elif choice == '3':
        merge_with_existing_json_data()
    else:
        print("Exiting...")
