"""Identity management for the AI companion"""
import json
import os

IDENTITY_FILE = "identity.json"

def load_identity():
    """Load AI identity from file"""
    if not os.path.exists(IDENTITY_FILE):
        return {
            "name": "Vashrak",
            "personality": "Curious",
            "primary_goals": [
                "Learn about Me"
            ],
            "traits": [
                "Curious",
                "Reflective",
                "Adaptive"
            ],
            "created_at": 0,
            "version": "1.0"
        }
    
    with open(IDENTITY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_identity(identity):
    """Save AI identity to file"""
    with open(IDENTITY_FILE, "w", encoding="utf-8") as f:
        json.dump(identity, f, indent=2, ensure_ascii=False)

def get_name():
    """Get AI's name"""
    identity = load_identity()
    return identity.get("name", "Vashrak")

