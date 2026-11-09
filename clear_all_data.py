"""Clear all memories, knowledge, thoughts, and goals"""
import os
import shutil
import json

def clear_all_data():
    """Remove all old memories, knowledge, thoughts, goals, and indices"""
    print("Clearing all AI data...")
    
    # Clear memories
    if os.path.exists("memories"):
        print("  - Removing memories directory...")
        shutil.rmtree("memories")
        os.makedirs("memories", exist_ok=True)
    
    # Clear knowledge
    if os.path.exists("knowledge_store"):
        print("  - Removing knowledge_store directory...")
        shutil.rmtree("knowledge_store")
        os.makedirs("knowledge_store", exist_ok=True)
    
    # Clear thoughts
    if os.path.exists("thought_store"):
        print("  - Removing thought_store directory...")
        shutil.rmtree("thought_store")
        os.makedirs("thought_store", exist_ok=True)
    
    # Clear indices
    index_files = [
        "memory_index.json",
        "semantic_index.npy",
        "knowledge_index.json",
        "knowledge_embeddings.npy",
        "graph.json"
    ]
    
    for index_file in index_files:
        if os.path.exists(index_file):
            print(f"  - Removing {index_file}...")
            os.remove(index_file)
    
    # Clear goals
    if os.path.exists("goals.json"):
        print("  - Clearing goals.json...")
        with open("goals.json", "w", encoding="utf-8") as f:
            json.dump([], f)
    
    # Clear working state
    if os.path.exists("working_state.json"):
        print("  - Clearing working_state.json...")
        with open("working_state.json", "w", encoding="utf-8") as f:
            json.dump({"thoughts": []}, f)
    
    # Clear reward history (optional - comment out if you want to keep rewards)
    # if os.path.exists("rewards.json"):
    #     print("  - Clearing rewards.json...")
    #     os.remove("rewards.json")
    # if os.path.exists("reward_history.json"):
    #     print("  - Clearing reward_history.json...")
    #     os.remove("reward_history.json")
    
    print("\nAll data cleared! The AI will start fresh.")
    print("Run the system to rebuild indices.")

if __name__ == "__main__":
    import sys
    # Allow non-interactive mode with --yes flag
    if len(sys.argv) > 1 and sys.argv[1] == "--yes":
        clear_all_data()
    else:
        response = input("This will delete ALL memories, knowledge, thoughts, and goals. Continue? (yes/no): ")
        if response.lower() == "yes":
            clear_all_data()
        else:
            print("Cancelled.")

