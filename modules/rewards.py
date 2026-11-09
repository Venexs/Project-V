"""Rewards system for conditioning LLM responses based on human feedback"""
import json
import os
import time
from typing import List, Dict, Tuple
from collections import defaultdict

REWARDS_FILE = "rewards.json"
REWARD_HISTORY_FILE = "reward_history.json"

def load_rewards() -> Dict:
    """Load reward data"""
    if not os.path.exists(REWARDS_FILE):
        return {
            "positive_patterns": [],
            "negative_patterns": [],
            "response_weights": {},
            "total_rewards": 0,
            "positive_count": 0,
            "negative_count": 0
        }
    with open(REWARDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_rewards(rewards: Dict):
    """Save reward data"""
    with open(REWARDS_FILE, "w", encoding="utf-8") as f:
        json.dump(rewards, f, indent=2, ensure_ascii=False)

def load_reward_history() -> List[Dict]:
    """Load reward history"""
    if not os.path.exists(REWARD_HISTORY_FILE):
        return []
    with open(REWARD_HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_reward_history(history: List[Dict]):
    """Save reward history"""
    with open(REWARD_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def record_reward(user_input: str, ai_response: str, reward: float, feedback_type: str = "implicit"):
    """
    Record a reward signal.
    reward: positive (1.0), negative (-1.0), or neutral (0.0)
    feedback_type: "implicit" (inferred from interaction), "explicit" (user directly provided)
    """
    rewards = load_rewards()
    history = load_reward_history()
    
    # Record in history
    history_entry = {
        "user_input": user_input,
        "ai_response": ai_response,
        "reward": reward,
        "feedback_type": feedback_type,
        "timestamp": time.time()
    }
    history.append(history_entry)
    
    # Keep only last 1000 entries
    if len(history) > 1000:
        history = history[-1000:]
    
    # Update reward statistics
    rewards["total_rewards"] += reward
    if reward > 0:
        rewards["positive_count"] += 1
    elif reward < 0:
        rewards["negative_count"] += 1
    
    # Extract patterns from positive/negative responses
    if reward > 0:
        # Positive response - extract what made it good
        rewards["positive_patterns"].append({
            "input": user_input[:100],
            "response": ai_response[:100],
            "weight": reward
        })
        # Keep only last 100 positive patterns
        if len(rewards["positive_patterns"]) > 100:
            rewards["positive_patterns"] = rewards["positive_patterns"][-100:]
    elif reward < 0:
        # Negative response - extract what made it bad
        rewards["negative_patterns"].append({
            "input": user_input[:100],
            "response": ai_response[:100],
            "weight": abs(reward)
        })
        # Keep only last 100 negative patterns
        if len(rewards["negative_patterns"]) > 100:
            rewards["negative_patterns"] = rewards["negative_patterns"][-100:]
    
    # Update response weights (simple frequency-based)
    response_key = ai_response[:50].lower()
    if response_key not in rewards["response_weights"]:
        rewards["response_weights"][response_key] = 0.0
    rewards["response_weights"][response_key] += reward * 0.1  # Decay factor
    
    save_rewards(rewards)
    save_reward_history(history)

def infer_reward_from_interaction(user_input: str, ai_response: str) -> float:
    """
    Infer reward from interaction patterns with regex word-boundary matching
    and negation/context handling.
    Returns: 1.0 (positive), -1.0 (negative), or 0.0 (neutral)
    """
    import re
    lower_input = user_input.lower().strip()
    lower_response = ai_response.lower().strip()

    # Explicit positive idioms that contain 'no'/'not' (must check before negatives)
    positive_idioms = [
        r"\bno problem\b", r"\bno worries\b", r"\bnot bad\b", r"\bnp\b"
    ]
    for pattern in positive_idioms:
        if re.search(pattern, lower_input):
            return 1.0

    # Positive signals (word boundary match, not substring match)
    positive_signals = [
        r"\byes\b", r"\byeah\b", r"\bgood\b", r"\bgreat\b", r"\bthanks?\b",
        r"\bthank you\b", r"\bcorrect\b", r"\bright\b", r"\bexactly\b",
        r"\bperfect\b", r"\blove\b", r"\blike\b", r"\bcool\b",
        r"\bawesome\b", r"\bnice\b"
    ]

    # Negative signals (word boundary match, avoids matching inside 'knowledge', 'now', etc.)
    negative_signals = [
        r"\bwrong\b", r"\bbad\b", r"\bstop\b", r"\bdon'?t\b",
        r"\bincorrect\b", r"\bhate\b", r"\bdislike\b", r"\bterrible\b",
        r"\bawful\b", r"\bstupid\b", r"\bdumb\b", r"\bnot what i\b", r"\bthat'?s not\b"
    ]

    # Check for positive signals in user input
    if any(re.search(pat, lower_input) for pat in positive_signals):
        return 1.0

    # Check for negative signals in user input
    if any(re.search(pat, lower_input) for pat in negative_signals):
        return -1.0

    # Check if response is too long (negative)
    if len(ai_response) > 150:
        return -0.3

    # Check if response is helpful/assistant-like (negative for self-concerned AI)
    helpful_phrases = [
        "what do you want", "how can i help", "what can i do",
        "let's talk", "let's explore", "what about you"
    ]
    if any(phrase in lower_response for phrase in helpful_phrases):
        return -1.0

    # Default neutral
    return 0.0

def get_reward_conditioning() -> str:
    """
    Get conditioning text based on reward history to guide LLM responses.
    """
    rewards = load_rewards()
    
    if rewards["total_rewards"] == 0:
        return ""  # No rewards yet
    
    # Calculate reward ratio
    total_interactions = rewards["positive_count"] + rewards["negative_count"]
    if total_interactions == 0:
        return ""
    
    positive_ratio = rewards["positive_count"] / total_interactions if total_interactions > 0 else 0
    
    conditioning = []
    
    # Add positive patterns guidance
    if rewards["positive_patterns"]:
        recent_positive = rewards["positive_patterns"][-5:]  # Last 5 positive
        if recent_positive:
            conditioning.append("\nRecent responses that were well-received:")
            for pattern in recent_positive:
                conditioning.append(f"- When asked '{pattern['input']}', responding like '{pattern['response'][:50]}' was positive")
    
    # Add negative patterns to avoid
    if rewards["negative_patterns"]:
        recent_negative = rewards["negative_patterns"][-5:]  # Last 5 negative
        if recent_negative:
            conditioning.append("\nRecent responses that were poorly received (AVOID these):")
            for pattern in recent_negative:
                conditioning.append(f"- When asked '{pattern['input']}', responding like '{pattern['response'][:50]}' was negative")
    
    # Overall guidance
    if positive_ratio > 0.6:
        conditioning.append("\nYour recent responses have been mostly well-received. Continue in this style.")
    elif positive_ratio < 0.4:
        conditioning.append("\nYour recent responses have been mostly poorly received. Adjust your approach.")
    
    return "\n".join(conditioning)

def get_response_weight(response: str) -> float:
    """Get weight for a response based on reward history"""
    rewards = load_rewards()
    response_key = response[:50].lower()
    return rewards["response_weights"].get(response_key, 0.0)

