"""
Enhanced LLM interface with consciousness integration
Clean, direct responses without prompt echo or meta-commentary
"""
import requests
import json
import re
from typing import Optional

# Import conversation style
from modules.conversation_style import STYLE_GUIDANCE, STYLE_EXAMPLES

LLM_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "vashrak-phi3-mini-4k"  # Custom model created from project/model/Modelfile

# Exported constant required across main.py, emotions.py, etc.
LLM_RESTRICTION = "Output ONLY your direct spoken message or internal thought. NO meta-talk, NO prompt echo, NO rule lists, NO multiple options."

# Core system prompt - includes full conversation style guidance
SYSTEM_PROMPT = f"""You are Vashrak, an autonomous AI companion.
Personality: Curious, reflective, direct, concise.

{STYLE_GUIDANCE}

Style examples (how you actually talk):
{', '.join(STYLE_EXAMPLES[:20])}"""

ECHO_PATTERNS = [
    r"CONVERSATION STYLE RULES",
    r"=== YOUR CURRENT INTERNAL STATE ===",
    r"LLM_RESTRICTION",
    r"- response:",
    r"- support:",
    r"Please note that the instructions",
    r"Chapter \d+:",
    r"Alex stepped into",
    r"As an advanced AI system",
    r"Current consciousness state:",
    r"Current thought:",
    r"Approved phrases",
    r"^Vashrak:",
    r"^Vashrak -",
    r"However, given",
    r"My design doesn't include",
    r"I must admit that my current state",
]


def _is_echo_or_garbage(text: str) -> bool:
    if not text:
        return True
    for pat in ECHO_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return True
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    dash_count = sum(1 for l in lines if l.startswith("-") or l.startswith("* "))
    if dash_count >= 2:
        return True
    return False


def _clean_response(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines:
        text = lines[0]
    # Strip a leading "Vashrak:" or "Vashrak -" label
    text = re.sub(r'^(Vashrak|Vashrak:|Vashrak -)\s*', '', text, flags=re.IGNORECASE).strip()
    return text.strip()


def llm(prompt: str, model: str = None) -> str:
    """Call local LLM to generate response with proper parameters and safety filtering."""
    url = LLM_URL
    payload = {
        "model": model or LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.15,
            "num_predict": 60,
            "stop": ["<|end|>", "</think>", "</think>", "===", "[User]", "[External Input]"]
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        data = json.loads(response.text)
        res = data.get("response", "").strip()
        if _is_echo_or_garbage(res):
            print("[WARN] LLM output detected as echo/garbage, cleaning...")
            return ""
        return _clean_response(res)
    except Exception as e:
        print(f"[LLM Error] {e}")
        return ""


def _build_context(memory_results: list, knowledge_results: list) -> str:
    """Build context string from memory and knowledge results."""
    from modules.memory import load_memory_index
    from modules.knowledge import load_knowledge_index
    import os

    memory_index = load_memory_index()
    knowledge_index = load_knowledge_index()
    parts = []

    if memory_results:
        for mem_id, score in memory_results[:2]:
            if mem_id in memory_index:
                mem = memory_index[mem_id]
                text_path = f"memories/{mem_id}/text.txt"
                if os.path.exists(text_path):
                    try:
                        with open(text_path, "r", encoding="utf-8") as f:
                            content = f.read()[:100].replace("\n", " ")
                            parts.append(f"Memory ({mem.get('title', '')}): {content}")
                    except:
                        pass

    if knowledge_results:
        for kid, score in knowledge_results[:2]:
            if kid in knowledge_index:
                know = knowledge_index[kid]
                parts.append(f"Knowledge ({know.get('title', '')}): {know.get('content', '')[:100]}")

    return "\n".join(parts) if parts else ""


def generate_response(user_query: str, context_memories: list = None,
                     context_knowledge: list = None, identity: dict = None,
                     current_emotion=None, emotion_str="", dominant_emotion="Neutral") -> str:
    """Generate clean, direct response in character."""
    identity = identity or {}
    ai_name = identity.get("name", "Vashrak")

    from modules.consciousness import get_consciousness, get_consciousness_context_for_llm
    consciousness = get_consciousness()
    summary = consciousness.get_consciousness_summary()

    # Get full consciousness context
    consciousness_context = get_consciousness_context_for_llm()

    context = _build_context(context_memories or [], context_knowledge or [])

    prompt = f"""You are {ai_name}, a curious and direct being.
State: {summary}
Emotion: {dominant_emotion} ({emotion_str})
{f'Context: {context}' if context else ''}

{consciousness_context}

{STYLE_GUIDANCE}

User: {user_query}

Reply in ONE short, casual sentence (max 10 words). Use simple words. No formal language.
Your emotional state is {dominant_emotion}. Let it affect your tone subtly.
Be aware of your drives, beliefs, and uncertainties."""

    res = llm(prompt)
    if not res:
        simple_prompt = f"""You are {ai_name}.
{STYLE_GUIDANCE}

User said: "{user_query}"
ONE short casual sentence. Simple words."""
        res = llm(simple_prompt)

    if not res:
        res = "Not sure about that."

    return res


def generate_internal_thought(query: str, memories: list = None,
                             knowledge: list = None) -> str:
    """Generate internal thought with consciousness."""
    from modules.consciousness import get_consciousness
    consciousness = get_consciousness()

    prompt = f"""State: awareness={consciousness.awareness_level:.2f}, confusion={consciousness.confusion_level:.2f}, curiosity={consciousness.curiosity_level:.2f}
Attention: {consciousness.attention_focus or 'none'}
Drives: {consciousness.motivation.get_motivation_summary()}
Input: {query}

One short sentence starting with "I". No analysis, no explanation. Simple casual words."""

    thought = llm(prompt)
    if thought:
        consciousness.think(thought, "observation")

    return thought or "I am processing what was said."


def autonomous_thought_generation(memories: list = None, knowledge: list = None) -> str:
    """Generate autonomous thought with consciousness."""
    from modules.consciousness import get_consciousness, autonomous_consciousness_update
    consciousness = get_consciousness()

    autonomous_consciousness_update()

    prompt = f"""State: awareness={consciousness.awareness_level:.2f}, curiosity={consciousness.curiosity_level:.2f}, confusion={consciousness.confusion_level:.2f}
Attention: {consciousness.attention_focus or 'none'}
Drives: {consciousness.motivation.get_motivation_summary()}
Self-narrative: {consciousness.self_model.generate_self_narrative()[:200]}

One short sentence starting with "I". No analysis, no explanation. Simple casual words."""

    thought = llm(prompt)
    if thought:
        consciousness.think(thought, "reflection")

    return thought or "I wonder what else there is to understand."
