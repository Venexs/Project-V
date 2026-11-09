"""
Initialize the Vashrak AI system.
Creates necessary directories and initial files.
"""
import os

def initialize():
    """Initialize system directories and files"""
    directories = [
        "memories",
        "knowledge_store",
        "thought_store"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"[OK] Created directory: {directory}")
    
    # Initialize empty thought store
    import json
    thought_store_path = "thought_store/thoughts.json"
    if not os.path.exists(thought_store_path):
        with open(thought_store_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        print(f"[OK] Created file: {thought_store_path}")
    
    # Initialize empty goals
    goals_path = "goals.json"
    if not os.path.exists(goals_path):
        with open(goals_path, "w", encoding="utf-8") as f:
            json.dump({"active_goals": []}, f, indent=2)
        print(f"[OK] Created file: {goals_path}")
    
    # Initialize empty working state
    working_path = "working_state.json"
    if not os.path.exists(working_path):
        with open(working_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        print(f"[OK] Created file: {working_path}")
    
    print("\n[OK] System initialized successfully!")

if __name__ == "__main__":
    initialize()

