"""Thought and goal management with autonomous creation (Hardened)"""

import os
import json
import time
import tempfile
from typing import List, Dict, Optional, Any

THOUGHT_STORE_DIR = "thought_store"
THOUGHT_STORE_FILE = os.path.join(THOUGHT_STORE_DIR, "thoughts.json")
WORKING_STATE_FILE = "working_state.json"
GOALS_FILE = "goals.json"


def _atomic_write(path: str, data: Any):
    """Atomically write JSON to path (write to temp then rename)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".tmp_", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except Exception:
            pass
        raise


def safe_list(value):
    """Ensure value is a list of strings (best-effort)."""
    if isinstance(value, list):
        # filter non-strings and strip
        return [str(v).strip() for v in value if isinstance(v, (str, int, float)) and str(v).strip()]
    if isinstance(value, (str, int, float)):
        s = str(value).strip()
        return [s] if s else []
    return []


def _validate_list_of_dicts(items):
    """Return filtered list keeping only dict items."""
    if not isinstance(items, list):
        return []
    return [i for i in items if isinstance(i, dict)]


def load_thoughts() -> List[Dict]:
    """Load thoughts from store - always returns a list (filters invalid items)."""
    os.makedirs(THOUGHT_STORE_DIR, exist_ok=True)
    if not os.path.exists(THOUGHT_STORE_FILE):
        return []

    try:
        with open(THOUGHT_STORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[WARN] Error loading thoughts.json: {e} — resetting to empty list")
        try:
            _atomic_write(THOUGHT_STORE_FILE, [])
        except Exception as exc:
            print(f"[ERROR] Failed to write empty thoughts.json: {exc}")
        return []

    # Normalize formats
    if isinstance(data, list):
        valid = _validate_list_of_dicts(data)
        if len(valid) != len(data):
            print(f"[WARN load_thoughts] Filtered out {len(data)-len(valid)} non-dict items")
            try:
                _atomic_write(THOUGHT_STORE_FILE, valid)
            except Exception as exc:
                print(f"[ERROR] Could not save cleaned thoughts.json: {exc}")
        return valid

    if isinstance(data, dict):
        # old format might use {'thoughts': [...]}
        if "thoughts" in data and isinstance(data["thoughts"], list):
            valid = _validate_list_of_dicts(data["thoughts"])
            try:
                _atomic_write(THOUGHT_STORE_FILE, valid)
            except Exception as exc:
                print(f"[ERROR] Could not migrate thoughts dict -> list: {exc}")
            return valid
        else:
            print(f"[WARN load_thoughts] thoughts.json is a dict but not expected shape (keys: {list(data.keys())}), resetting to empty list")
            try:
                _atomic_write(THOUGHT_STORE_FILE, [])
            except Exception as exc:
                print(f"[ERROR] Could not reset thoughts.json: {exc}")
            return []

    # Unexpected types
    print(f"[WARN load_thoughts] thoughts.json contains unexpected type {type(data)}, resetting to empty list")
    try:
        _atomic_write(THOUGHT_STORE_FILE, [])
    except Exception as exc:
        print(f"[ERROR] Could not reset thoughts.json: {exc}")
    return []


def save_thoughts(thoughts: List[Dict]):
    """Save thoughts to store (atomic)."""
    if not isinstance(thoughts, list):
        raise ValueError("thoughts must be a list")
    _atomic_write(THOUGHT_STORE_FILE, thoughts)


def _normalize_emotion_input(emotion: Optional[Dict[str, float]], default_getter):
    """
    Normalize emotion dict to expected keys. Accepts mixed-case keys.
    default_getter: callable that returns default emotion dict if emotion is None.
    """
    if emotion is None:
        return default_getter()

    # create lowercase-keyed dict for tolerant access
    lower = {k.lower(): float(v) if isinstance(v, (int, float)) else 0.0 for k, v in emotion.items() if isinstance(k, str)}
    return {
        "Happy": lower.get("happy", lower.get("happiness", 0.0)),
        "Sad": lower.get("sad", 0.0),
        "Anger": lower.get("anger", 0.0),
        "Fear": lower.get("fear", 0.0),
        "Disgust": lower.get("disgust", 0.0),
        "Surprise": lower.get("surprise", 0.0),
    }


def add_thought(content: str, strength: float = 0.5, decay_rate: float = 0.02, emotion: Dict[str, float] = None):
    """Add a new thought with optional 6D emotion graph"""
    # lazy import so module not required for tests; keep same usage as original
    from modules.emotions import get_default_emotion, create_emotion_graph

    thoughts = load_thoughts()

    # CRITICAL: Ensure thoughts is ALWAYS a list, not a dict
    if not isinstance(thoughts, list):
        print(f"[ERROR add_thought] thoughts is not a list: {type(thoughts)}. Resetting to empty list.")
        thoughts = []
        try:
            _atomic_write(THOUGHT_STORE_FILE, [])
        except Exception as exc:
            print(f"[ERROR] Could not reset thoughts file: {exc}")

    # Normalize emotion robustly
    normalized = _normalize_emotion_input(emotion, get_default_emotion)
    # create_emotion_graph expects keyword args; map our normalized dict
    emotion_graph = create_emotion_graph(
        happy=normalized.get("Happy", 0.0),
        sad=normalized.get("Sad", 0.0),
        anger=normalized.get("Anger", 0.0),
        fear=normalized.get("Fear", 0.0),
        disgust=normalized.get("Disgust", 0.0),
        surprise=normalized.get("Surprise", 0.0)
    )

    # Check if thought already exists to reinforce it
    reinforced = False
    content_lower = content.strip().lower()
    for existing in thoughts:
        if isinstance(existing, dict) and existing.get("content", "").strip().lower() == content_lower:
            existing["strength"] = min(1.0, float(existing.get("strength", 0.5)) + float(strength))
            existing["timestamp"] = float(time.time())
            thought = existing
            reinforced = True
            break

    if not reinforced:
        thought = {
            "content": content,
            "strength": float(strength),
            "timestamp": float(time.time()),
            "decay_rate": float(decay_rate),
            "emotion": emotion_graph
        }
        # ensure list again
        if not isinstance(thoughts, list):
            thoughts = []
        thoughts.insert(0, thought)
    try:
        save_thoughts(thoughts)
    except Exception as e:
        print(f"[ERROR add_thought] Failed to save thoughts: {e}")
    return thought


def decay_and_consolidate_thoughts(min_strength: float = 0.65, min_survival: float = 0.15):
    """
    Decay thoughts and consolidate strong ones into memories.
    Returns list of thoughts that should become memories.
    """
    thoughts = load_thoughts()
    if not isinstance(thoughts, list):
        print(f"[WARN] decay_and_consolidate_thoughts: thoughts is not a list: {type(thoughts)}, using empty list")
        thoughts = []

    new_thoughts = []
    memories_to_create = []
    now = time.time()

    for t in thoughts:
        if not isinstance(t, dict):
            continue
        # require fields
        if not all(k in t for k in ("timestamp", "strength", "decay_rate", "content")):
            continue
        try:
            age_hours = max(0.0, (now - float(t["timestamp"])) / 3600.0)
            # decay model: exponential per hour
            decay_rate = float(t.get("decay_rate", 0.0))
            strength = float(t.get("strength", 0.0)) * ((1.0 - decay_rate) ** age_hours if decay_rate < 1.0 else 0.0)

            if strength >= min_strength:
                # Strong thought consolidates into permanent memory; remove from active thoughts
                memories_to_create.append(t["content"])
            elif strength > min_survival:
                # Update decayed strength and retain
                t["strength"] = max(0.0, strength)
                new_thoughts.append(t)
        except (KeyError, TypeError, ValueError) as e:
            print(f"[WARN] Error processing thought: {e}, skipping")
            continue

    try:
        save_thoughts(new_thoughts)
    except Exception as e:
        print(f"[ERROR] Could not save decayed thoughts: {e}")

    return memories_to_create


def load_working_state() -> List[Dict]:
    """Load working state - always returns a list (filters invalid items)."""
    if not os.path.exists(WORKING_STATE_FILE):
        return []

    try:
        with open(WORKING_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[WARN] Error loading working_state.json: {e} — resetting to empty list")
        try:
            _atomic_write(WORKING_STATE_FILE, [])
        except Exception as exc:
            print(f"[ERROR] Could not reset working_state.json: {exc}")
        return []

    if isinstance(data, list):
        valid = _validate_list_of_dicts(data)
        if len(valid) != len(data):
            print(f"[WARN load_working_state] Filtered out {len(data)-len(valid)} non-dict items")
            try:
                _atomic_write(WORKING_STATE_FILE, valid)
            except Exception as exc:
                print(f"[ERROR] Could not save cleaned working_state.json: {exc}")
        return valid

    if isinstance(data, dict):
        # support {'items': [...]}
        if "items" in data and isinstance(data["items"], list):
            valid = _validate_list_of_dicts(data["items"])
            try:
                _atomic_write(WORKING_STATE_FILE, valid)
            except Exception as exc:
                print(f"[ERROR] Could not migrate working_state dict->list: {exc}")
            return valid
        else:
            print(f"[WARN] working_state.json is dict but not expected shape (keys: {list(data.keys())}), resetting")
            try:
                _atomic_write(WORKING_STATE_FILE, [])
            except Exception as exc:
                print(f"[ERROR] Could not reset working_state.json: {exc}")
            return []

    print(f"[WARN] working_state.json contains unexpected type {type(data)}, resetting to empty list")
    try:
        _atomic_write(WORKING_STATE_FILE, [])
    except Exception as exc:
        print(f"[ERROR] Could not reset working_state.json: {exc}")
    return []


def save_working_state(working: List[Dict]):
    """Save working state (atomic)."""
    if not isinstance(working, list):
        raise ValueError("working must be a list")
    _atomic_write(WORKING_STATE_FILE, working)


def add_working_thought(content: str, thought_type: str = "note", importance: float = 0.5, ttl: int = 600, emotion: Dict[str, float] = None):
    """Add to working state with optional 6D emotion graph"""
    from modules.emotions import get_default_emotion, create_emotion_graph

    working = load_working_state()

    if not isinstance(working, list):
        print(f"[ERROR add_working_thought] working is not a list: {type(working)}. Resetting.")
        working = []
        try:
            _atomic_write(WORKING_STATE_FILE, [])
        except Exception as exc:
            print(f"[ERROR] Could not reset working_state file: {exc}")

    normalized = _normalize_emotion_input(emotion, get_default_emotion)
    emotion_graph = create_emotion_graph(
        happy=normalized.get("Happy", 0.0),
        sad=normalized.get("Sad", 0.0),
        anger=normalized.get("Anger", 0.0),
        fear=normalized.get("Fear", 0.0),
        disgust=normalized.get("Disgust", 0.0),
        surprise=normalized.get("Surprise", 0.0)
    )

    t = {
        "id": f"T{int(time.time() * 1000)}",
        "content": content,
        "type": thought_type,
        "importance": float(importance),
        "created_at": float(time.time()),
        "ttl_seconds": int(ttl),
        "emotion": emotion_graph
    }

    if not isinstance(working, list):
        working = []

    working.insert(0, t)
    prune_working(working)
    try:
        save_working_state(working)
    except Exception as e:
        print(f"[ERROR add_working_thought] Failed to save working state: {e}")
    return t


def prune_working(working: List[Dict], max_items: int = 20):
    """Prune expired working thoughts (in-place)."""
    now = time.time()
    try:
        working[:] = [
            t for t in working
            if isinstance(t, dict) and now - float(t.get("created_at", 0)) < int(t.get("ttl_seconds", 0))
        ]
    except Exception as e:
        print(f"[WARN prune_working] Error while pruning: {e}")
    if len(working) > max_items:
        working[:] = working[:max_items]


def load_goals() -> Dict:
    """Load goals. Return dict with 'active_goals' key (migrate/clean legacy formats)."""
    if not os.path.exists(GOALS_FILE):
        return {"active_goals": []}

    try:
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[WARN] Error loading goals.json: {e} — resetting to default")
        try:
            _atomic_write(GOALS_FILE, {"active_goals": []})
        except Exception as exc:
            print(f"[ERROR] Could not reset goals.json: {exc}")
        return {"active_goals": []}

    # Accept expected dict
    if isinstance(data, dict):
        ag = data.get("active_goals")
        if ag is None:
            # Maybe old format had keys directly as goal list
            if any(isinstance(v, list) for v in data.values()):
                # not sure — fallback to default
                print("[WARN load_goals] goals.json dict with unexpected structure, normalizing to {'active_goals': []}")
                try:
                    _atomic_write(GOALS_FILE, {"active_goals": []})
                except Exception as exc:
                    print(f"[ERROR] Could not normalize goals.json: {exc}")
                return {"active_goals": []}
            else:
                return {"active_goals": []}
        if not isinstance(ag, list):
            print(f"[WARN load_goals] 'active_goals' is not a list ({type(ag)}). Resetting to []")
            try:
                _atomic_write(GOALS_FILE, {"active_goals": []})
            except Exception as exc:
                print(f"[ERROR] Could not save normalized goals.json: {exc}")
            return {"active_goals": []}
        # Filter to dicts
        valid = _validate_list_of_dicts(ag)
        if len(valid) != len(ag):
            print(f"[WARN load_goals] Filtered out {len(ag)-len(valid)} non-dict goals")
            try:
                _atomic_write(GOALS_FILE, {"active_goals": valid})
            except Exception as exc:
                print(f"[ERROR] Could not save cleaned goals.json: {exc}")
        return {"active_goals": valid}

    # Legacy format: list -> migrate into dict
    if isinstance(data, list):
        print("[WARN load_goals] goals.json is a list (legacy) — migrating into {'active_goals': [...]}")
        valid = _validate_list_of_dicts(data)
        try:
            _atomic_write(GOALS_FILE, {"active_goals": valid})
        except Exception as exc:
            print(f"[ERROR] Could not migrate goals.json: {exc}")
        return {"active_goals": valid}

    print(f"[WARN load_goals] goals.json has unexpected type {type(data)}, resetting to default")
    try:
        _atomic_write(GOALS_FILE, {"active_goals": []})
    except Exception as exc:
        print(f"[ERROR] Could not reset goals.json: {exc}")
    return {"active_goals": []}


def save_goals(goals: Dict):
    """Save goals (atomic). Expect dict with active_goals list."""
    if not isinstance(goals, dict):
        raise ValueError("goals must be a dict")
    # ensure key exists
    if "active_goals" not in goals or not isinstance(goals["active_goals"], list):
        goals["active_goals"] = []
    _atomic_write(GOALS_FILE, goals)


def add_goal(name: str, importance: float = 0.5, keywords: List[str] = None):
    """Add a new goal. Handles legacy/malformed goals.json gracefully."""
    goals = load_goals()

    # Ensure dict shape
    if not isinstance(goals, dict):
        print(f"[ERROR add_goal] goals is not a dict: {type(goals)}, resetting to default")
        goals = {"active_goals": []}

    if "active_goals" not in goals or not isinstance(goals["active_goals"], list):
        print(f"[WARN add_goal] active_goals missing or invalid, creating empty list")
        goals["active_goals"] = []

    # Normalize keywords
    if keywords is None:
        keywords = []
    elif not isinstance(keywords, list):
        if isinstance(keywords, str):
            keywords = [keywords]
        else:
            keywords = []

    keyword_list = safe_list(keywords)

    goal = {
        "name": name,
        "importance": float(importance),
        "keywords": keyword_list
    }

    goals["active_goals"].append(goal)
    try:
        save_goals(goals)
    except Exception as e:
        print(f"[ERROR add_goal] Failed to save goals: {e}")
    return goal


def apply_goal_bias(similarity: float, item_text: str) -> float:
    """Apply goal-based bias to similarity scores"""
    goals = load_goals()
    bias = 0.0

    for g in goals.get("active_goals", []):
        kws = g.get("keywords", [])
        if any(kw.lower() in item_text.lower() for kw in safe_list(kws)):
            bias += 0.1 * float(g.get("importance", 0.5))

    return similarity + bias
