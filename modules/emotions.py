"""6D Emotional Graph System
Emotions are represented as a 6-dimensional graph with values from 0.0 to 1.0
Axes: Happy, Sad, Anger, Fear, Disgust, Surprise
All values are rounded to 3 decimal places
"""
import json
import os
from typing import Dict, Optional

EMOTION_AXES = ["Happy", "Sad", "Anger", "Fear", "Disgust", "Surprise"]
EMOTION_FILE = "current_emotion.json"

def round_emotion(value: float) -> float:
    """Round emotion value to 3 decimal places, clamp to [0.0, 1.0]"""
    return round(max(0.0, min(1.0, float(value))), 3)

def create_emotion_graph(happy: float = 0.0, sad: float = 0.0, anger: float = 0.0,
                         fear: float = 0.0, disgust: float = 0.0, surprise: float = 0.0) -> Dict[str, float]:
    """
    Create a 6D emotion graph with all values in [0.0, 1.0], rounded to 3 decimals.
    """
    return {
        "Happy": round_emotion(happy),
        "Sad": round_emotion(sad),
        "Anger": round_emotion(anger),
        "Fear": round_emotion(fear),
        "Disgust": round_emotion(disgust),
        "Surprise": round_emotion(surprise)
    }

def get_default_emotion() -> Dict[str, float]:
    """Get default neutral emotion (all zeros)"""
    return create_emotion_graph()

def load_current_emotion() -> Dict[str, float]:
    """Load current emotion state from file"""
    if not os.path.exists(EMOTION_FILE):
        emotion = get_default_emotion()
        save_current_emotion(emotion)
        return emotion
    
    try:
        with open(EMOTION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all axes are present and valid
            emotion = create_emotion_graph(
                happy=data.get("Happy", 0.0),
                sad=data.get("Sad", 0.0),
                anger=data.get("Anger", 0.0),
                fear=data.get("Fear", 0.0),
                disgust=data.get("Disgust", 0.0),
                surprise=data.get("Surprise", 0.0)
            )
            return emotion
    except Exception as e:
        print(f"[Emotion] Error loading emotion: {e}, using default")
        return get_default_emotion()

def save_current_emotion(emotion: Dict[str, float]):
    """Save current emotion state to file"""
    # Ensure all values are properly rounded
    normalized = create_emotion_graph(
        happy=emotion.get("Happy", 0.0),
        sad=emotion.get("Sad", 0.0),
        anger=emotion.get("Anger", 0.0),
        fear=emotion.get("Fear", 0.0),
        disgust=emotion.get("Disgust", 0.0),
        surprise=emotion.get("Surprise", 0.0)
    )
    
    try:
        with open(EMOTION_FILE, "w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Emotion] Error saving emotion: {e}")

def update_emotion(emotion: Dict[str, float], updates: Dict[str, float]):
    """
    Update emotion graph with new values.
    Updates are additive (clamped to [0.0, 1.0]).
    """
    new_emotion = {}
    for axis in EMOTION_AXES:
        current = emotion.get(axis, 0.0)
        change = updates.get(axis, 0.0)
        new_emotion[axis] = round_emotion(current + change)
    
    return new_emotion

def set_emotion(emotion: Dict[str, float], values: Dict[str, float]):
    """
    Set emotion graph to specific values (replaces current).
    """
    return create_emotion_graph(
        happy=values.get("Happy", emotion.get("Happy", 0.0)),
        sad=values.get("Sad", emotion.get("Sad", 0.0)),
        anger=values.get("Anger", emotion.get("Anger", 0.0)),
        fear=values.get("Fear", emotion.get("Fear", 0.0)),
        disgust=values.get("Disgust", emotion.get("Disgust", 0.0)),
        surprise=values.get("Surprise", emotion.get("Surprise", 0.0))
    )

def get_dominant_emotion(emotion: Dict[str, float]) -> str:
    """Get the axis with the highest value"""
    if not emotion:
        return "Neutral"
    
    max_axis = max(EMOTION_AXES, key=lambda axis: emotion.get(axis, 0.0))
    max_value = emotion.get(max_axis, 0.0)
    
    if max_value < 0.1:
        return "Neutral"
    
    return max_axis

def get_emotion_intensity(emotion: Dict[str, float]) -> float:
    """Get overall emotion intensity (max value across all axes)"""
    if not emotion:
        return 0.0
    return round_emotion(max(emotion.get(axis, 0.0) for axis in EMOTION_AXES))

def emotion_to_string(emotion: Dict[str, float]) -> str:
    """Convert emotion graph to readable string"""
    parts = []
    for axis in EMOTION_AXES:
        value = emotion.get(axis, 0.0)
        if value > 0.0:
            parts.append(f"{axis}: {value:.3f}")
    
    if not parts:
        return "Neutral (all 0.000)"
    
    return ", ".join(parts)

def parse_emotion_from_text(text: str, current_emotion: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """
    Parse emotion changes from text using LLM.
    Returns a dict of changes to apply to current emotion.
    """
    if current_emotion is None:
        current_emotion = load_current_emotion()

    # Use LLM to determine emotion changes
    from modules.llm import llm, LLM_RESTRICTION

    prompt = f"""{LLM_RESTRICTION}

Analyze this text and determine how it should affect a 6D emotional graph.
The axes are: Happy, Sad, Anger, Fear, Disgust, Surprise
All values range from 0.0 to 1.0 (3 decimal places max).

Text: "{text}"

Current emotion state:
{emotion_to_string(current_emotion)}

Respond with ONLY a JSON object in this exact format:
{{
  "Happy": 0.0,
  "Sad": 0.0,
  "Anger": 0.0,
  "Fear": 0.0,
  "Disgust": 0.0,
  "Surprise": 0.0
}}

These values represent CHANGES to apply (can be positive or negative, but will be clamped to [0.0, 1.0]).
If no change is needed, use 0.0 for all axes.
"""

    try:
        response = llm(prompt).strip()
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            emotion_changes = json.loads(json_match.group())
            # Return as changes dict, not normalized graph
            return {
                "Happy": emotion_changes.get("Happy", 0.0),
                "Sad": emotion_changes.get("Sad", 0.0),
                "Anger": emotion_changes.get("Anger", 0.0),
                "Fear": emotion_changes.get("Fear", 0.0),
                "Disgust": emotion_changes.get("Disgust", 0.0),
                "Surprise": emotion_changes.get("Surprise", 0.0)
            }
    except Exception as e:
        print(f"[Emotion] Error parsing emotion from text: {e}")

    # Return zero changes on error
    return {"Happy": 0.0, "Sad": 0.0, "Anger": 0.0, "Fear": 0.0, "Disgust": 0.0, "Surprise": 0.0}


def decay_emotions(emotion: Dict[str, float], decay_rate: float = 0.02) -> Dict[str, float]:
    """Gradually decay emotions towards neutral over time"""
    decayed = {}
    for axis in EMOTION_AXES:
        current = emotion.get(axis, 0.0)
        # Move towards 0.0
        if current > 0:
            decayed[axis] = round_emotion(current * (1 - decay_rate))
        else:
            decayed[axis] = round_emotion(max(0.0, current + decay_rate))
    return decayed


def emotion_to_consciousness(emotion: Dict[str, float]) -> Dict[str, float]:
    """Map emotion to consciousness adjustments"""
    adjustments = {}

    # High Fear/Anxiety → increase confusion
    fear_level = emotion.get("Fear", 0.0)
    if fear_level > 0.5:
        adjustments["confusion_delta"] = fear_level * 0.05

    # High Sad → decrease awareness slightly
    sad_level = emotion.get("Sad", 0.0)
    if sad_level > 0.5:
        adjustments["awareness_delta"] = -sad_level * 0.03

    # High Happy → increase awareness
    happy_level = emotion.get("Happy", 0.0)
    if happy_level > 0.5:
        adjustments["awareness_delta"] = happy_level * 0.04

    # High Surprise → increase curiosity
    surprise_level = emotion.get("Surprise", 0.0)
    if surprise_level > 0.5:
        adjustments["curiosity_delta"] = surprise_level * 0.03

    # High Anger → increase confusion
    anger_level = emotion.get("Anger", 0.0)
    if anger_level > 0.5:
        adjustments["confusion_delta"] = anger_level * 0.04

    return adjustments




