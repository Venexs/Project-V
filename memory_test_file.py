import json, os, numpy as np
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util
import threading

model = SentenceTransformer("all-MiniLM-L6-v2")

import torch
import requests
import json

import cv2
import face_recognition
import numpy as np
import sounddevice as sd
import soundfile as sf
import time
import os
import json


def llm(prompt: str) -> str:
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "zeroai",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=payload)
    data = json.loads(response.text)
    return data["response"]

# Load symbolic index
with open("memory_index.json", "r") as f:
    memory_index = json.load(f)

# Load semantic vectors
semantic_vectors = np.load("semantic_index.npy", allow_pickle=True).item()
# Format: {memory_id: np.array([embedding])}'

device = model.device  # "cuda" or "cpu"

# ================================================================== Memory

# Load semantic graph
with open("graph.json", "r") as f:
    memory_graph = json.load(f)

# Load working memory
try:
    with open("working_state.json", "r") as f:
        WORKING = json.load(f)
except:
    WORKING = []

def save_working():
    with open("working_state.json", "w") as f:
        json.dump(WORKING, f, indent=2)

def embed(text: str) -> np.ndarray:
    return model.encode(text, normalize_embeddings=True)

def retrieve_similar_memories(query, top_k=3):
    """
    Returns top_k memories as (memory_id, similarity) pairs
    """
    memory_ids = list(memory_index.keys())
    memory_texts = []

    for mid in memory_ids:
        meta = memory_index[mid]
        summary = meta.get("title", "") + ". " + ", ".join(meta.get("topics", []))
        memory_texts.append(summary)

    mem_embeddings = model.encode(memory_texts, convert_to_tensor=True)
    q_embedding = model.encode(query, convert_to_tensor=True)

    # Ensure both tensors on same device
    if mem_embeddings.device != q_embedding.device:
        q_embedding = q_embedding.to(mem_embeddings.device)

    scores = util.cos_sim(q_embedding, mem_embeddings)[0]  # similarity scores
    top = torch.topk(scores, k=min(top_k, len(memory_texts)))

    results = [(memory_ids[i], float(scores[i])) for i in top.indices]
    return results

def compute_activation(memory_id, similarity):
    meta = memory_index[memory_id]
    recency_days = (datetime.now().timestamp() - meta["last_accessed"]) / 86400
    recency_factor = np.exp(-recency_days / 30)  # decays over ~month
    emotion_factor = meta["emotion_intensity"]  # 0–1 float
    tag_weight = meta["tag_relevance"]           # precomputed average

    # Weighted combination
    return (
        similarity * 0.6
        + tag_weight * 0.2
        + recency_factor * 0.1
        + emotion_factor * 0.1
    )

def expand_graph_nodes(memory_id, depth=1):
    related = []
    frontier = [memory_id]
    for _ in range(depth):
        new_frontier = []
        for node in frontier:
            edges = memory_graph.get(node, [])
            for edge in edges:
                target = edge["target"]
                weight = edge["weight"]
                if weight > 0.7:         # threshold for “strong” association
                    related.append((target, weight))
                    new_frontier.append(target)
        frontier = new_frontier
    return related

def associative_recall(query):
    candidates = retrieve_similar_memories(query, top_k=5)
    activated = {}

    for mem_id, sim in candidates:
        act = compute_activation(mem_id, sim)
        activated[mem_id] = act

        # Graph traversal
        for related_id, w in expand_graph_nodes(mem_id, depth=1):
            act_related = act * w
            activated[related_id] = max(activated.get(related_id, 0), act_related)

    # Sort final activations
    ranked = sorted(activated.items(), key=lambda x: x[1], reverse=True)
    return ranked[:3]   # top 3 most activated memories

def summarize_memory(memory_id):
    with open(f"memories/{memory_id}/meta.json") as f:
        meta = json.load(f)
    
    # handle nested structure like {"M002": {...}}
    if memory_id in meta:
        meta = meta[memory_id]

    summary = f"{meta.get('title', 'Untitled')}: " \
               f"{meta.get('summary', 'No summary available')} " \
               f"(Emotion: {meta.get('dominant_emotion', 'Unknown')})"
    return summary

def generate_context(query):
    results = associative_recall(query) 
    context_snippets = [summarize_memory(mid) for mid, _ in results]
    return "\n".join(context_snippets)

# ====================================================================================== Knowledge


def retrieve_knowledge(query, top_k=3):
    """
    Returns top_k knowledge items as (knowledge_id, similarity) pairs
    """
    knowledge_ids = list(knowledge_index.keys())
    knowledge_texts = [knowledge_index[k]["content"] for k in knowledge_ids]

    emb_tensor = model.encode(knowledge_texts, convert_to_tensor=True)
    q_emb = model.encode(query, convert_to_tensor=True)

    # Make sure tensors are same dtype & device
    if emb_tensor.device != q_emb.device:
        q_emb = q_emb.to(emb_tensor.device)
    if emb_tensor.dtype != q_emb.dtype:
        q_emb = q_emb.to(emb_tensor.dtype)

    scores = util.cos_sim(q_emb, emb_tensor)[0]
    top = torch.topk(scores, k=min(top_k, len(knowledge_texts)))

    results = [(knowledge_ids[i], float(scores[i])) for i in top.indices]
    return results

def build_workspace(query):
    memory_results = retrieve_similar_memories(query, top_k=5)
    knowledge_results = retrieve_knowledge(query, top_k=5)

    # Filter out low relevance items
    memory_results = [(mid, s) for (mid, s) in memory_results if s >= 0.15]
    knowledge_results = [(kid, s) for (kid, s) in knowledge_results if s >= 0.15]

    if len(memory_results) == 0:
        memory_results = None
    if len(knowledge_results) == 0:
        knowledge_results = None

    internal_thoughts = generate_internal_thoughts(query, memory_results, knowledge_results)

    return {
        "memories": memory_results,
        "knowledge": knowledge_results,
        "internal_thoughts": internal_thoughts
    }



def store_working_thought(content, strength):
    """
    Stores a temporary thought with decay into thought_store/thoughts.json.
    Creates directories/files if missing.
    """
    import json, time, os

    path_dir = "thought_store"
    os.makedirs(path_dir, exist_ok=True)
    path = os.path.join(path_dir, "thoughts.json")

    # ensure file exists
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)

    with open(path, "r", encoding="utf-8") as f:
        try:
            thoughts = json.load(f)
        except Exception:
            thoughts = []

    thought = {
        "content": content,
        "strength": float(strength),
        "timestamp": time.time(),
        "decay_rate": 0.02
    }
    thoughts.insert(0, thought)  # newest first

    with open(path, "w", encoding="utf-8") as f:
        json.dump(thoughts, f, indent=2, ensure_ascii=False)

    # debug
    # print(f"[store_working_thought] saved to {path}: {thought['content'][:80]}")


def decay_and_consolidate_thoughts():
    import json, time

    path = "thought_store/thoughts.json"
    with open(path, "r") as f:
        thoughts = json.load(f)

    new_list = []
    for t in thoughts:
        age_hours = (time.time() - t["timestamp"]) / 3600
        strength = t["strength"] * (1 - t["decay_rate"]) ** age_hours

        # If strength is high enough → convert to a memory
        if strength > 0.75:
            create_new_memory_from_thought(t["content"])

        # Keep only surviving thoughts
        if strength > 0.15:
            t["strength"] = strength
            new_list.append(t)

    with open(path, "w") as f:
        json.dump(new_list, f, indent=2)

def apply_goal_bias(similarity, item_text):
    import json

    with open("goals.json", "r") as f:
        goals = json.load(f)["active_goals"]

    bias = 0
    for g in goals:
        if any(kw.lower() in item_text.lower() for kw in g["keywords"]):
            bias += 0.1 * g["importance"]

    return similarity + bias


def create_new_memory_from_thought(content):
    """
    Converts a strong thought into a new episodic memory.
    """

    import time, os, json
    mem_id = f"M{int(time.time())}"

    os.makedirs(f"memories/{mem_id}", exist_ok=True)
    meta = {
        "title": "Consolidated Thought",
        "summary": content,
        "people": [],
        "objects": [],
        "topics": ["Reflection"],
        "dominant_emotion": "Neutral",
        "emotion_intensity": 0.3,
        "last_accessed": time.time(),
        "tag_relevance": 0.6
    }

    with open(f"memories/{mem_id}/meta.json", "w") as f:
        json.dump(meta, f, indent=2)


def add_thought(content, type="note", importance=0.5, ttl=600):
    """
    Adds to in-memory/working_state.json AND to thought_store/thoughts.json for consolidation.
    """
    global WORKING

    t = {
        "id": f"T{int(time.time()*1000)}",
        "content": content,
        "type": type,
        "importance": float(importance),
        "created_at": time.time(),
        "ttl_seconds": int(ttl)
    }

    # insert to working buffer (in-memory + persisted)
    WORKING.insert(0, t)
    prune_working()
    save_working()
    
    # also persist into thought_store for consolidation pipeline
    try:
        # store a slightly different representation used by consolidation
        store_working_thought(content=content, strength=float(importance))
    except Exception as e:
        print(f"[WARN] failed to store working thought in thought_store: {e}")

    # quick confirmation print for dev
    # print(f"[add_thought] added: {t['id']} (imp {t['importance']})")

def debug_show_recent_thoughts(n=5):
    print("=== WORKING_STATE (top) ===")
    try:
        for t in WORKING[:n]:
            print(f"- {t['id']} {t['content'][:80]} (imp {t['importance']})")
    except Exception:
        print("No WORKING entries.")

    print("\n=== thought_store (top) ===")
    try:
        import json, os
        p = "thought_store/thoughts.json"
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                thoughts = json.load(f)
            for t in thoughts[:n]:
                print(f"- {t['timestamp']} {t['content'][:80]} (str {t['strength']})")
        else:
            print("thought_store file missing.")
    except Exception as e:
        print("Error reading thought_store:", e)


def prune_working():
    now = time.time()
    WORKING[:] = [
        t for t in WORKING
        if now - t["created_at"] < t["ttl_seconds"]
    ]
    if len(WORKING) > 20:
        WORKING[:] = WORKING[:20]


# Load knowledge
with open("knowledge_index.json", "r") as f:
    knowledge_index = json.load(f)

knowledge_embeddings = np.load("knowledge_embeddings.npy", allow_pickle=True).item()


# ====================================================================================== Face

def capture_user_audio_video(duration=5, audio_file="temp_audio.wav", video_file="temp_video.avi"):
    """
    Capture short video + audio from user.
    Returns face encoding and audio file path.
    """
    # --- Video Capture ---
    cap = cv2.VideoCapture(0)
    frames = []
    start_time = time.time()
    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret:
            continue
        frames.append(frame)
        cv2.imshow("Recording (Press 'q' to stop)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()

    # Save video
    if frames:
        height, width, _ = frames[0].shape
        out = cv2.VideoWriter(video_file, cv2.VideoWriter_fourcc(*'XVID'), 10, (width, height))
        for f in frames:
            out.write(f)
        out.release()

    # --- Face Encoding ---
    if frames:
        face_encodings = face_recognition.face_encodings(frames[0])
        if face_encodings:
            face_encoding = face_encodings[0]
        else:
            face_encoding = None
    else:
        face_encoding = None

    # --- Audio Capture ---
    fs = 44100
    print("Recording audio...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    sf.write(audio_file, audio, fs)

    return face_encoding, audio_file, video_file

def store_user_profile(face_encoding, audio_file, video_file, user_name=None):
    """
    Store captured user as memory + knowledge.
    """
    mem_id = f"M{int(time.time())}"
    os.makedirs(f"memories/{mem_id}", exist_ok=True)

    # Memory metadata
    meta = {
        "title": f"User: {user_name or 'Unknown'}",
        "people": [user_name or "Unknown"],
        "objects": ["Video", "Audio"],
        "topics": ["User Recognition", "Identity"],
        "dominant_emotion": "Neutral",
        "emotion_intensity": 0.3,
        "last_accessed": time.time(),
        "tag_relevance": 1.0,
        "face_encoding": face_encoding.tolist() if face_encoding is not None else None,
        "audio_file": audio_file,
        "video_file": video_file
    }

    with open(f"memories/{mem_id}/meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    # Also store knowledge about the user
    kid = f"K{int(time.time())}"
    knowledge_index[kid] = {
        "title": f"Profile: {user_name or 'Unknown'}",
        "keywords": ["user", "identity", "face-recognition"],
        "summary": f"Profile knowledge for {user_name or 'Unknown'}",
        "content": f"Face encoding stored, audio-video recorded for identity recognition.",
        "importance": 0.5,
        "last_updated": time.time()
    }

    # Save knowledge index
    with open("knowledge_index.json", "w") as f:
        json.dump(knowledge_index, f, indent=2)
    
    print(f"[Profile] User memory and knowledge stored: {user_name or 'Unknown'}")


def recognize_user(face_encoding, threshold=0.5):
    """
    Check if face matches existing memory.
    """
    for mem_id, meta in memory_index.items():
        if meta.get("face_encoding") is not None:
            stored_face = np.array(meta["face_encoding"])
            dist = np.linalg.norm(stored_face - face_encoding)
            if dist < threshold:
                return mem_id, meta["title"]
    return None, None

# ====================================================================================== Train of Thought

def generate_internal_thoughts(query, memories, knowledge):
    context_str = ""

    if memories:
        context_str += "Relevant memories:\n"
        for mid, score in memories:
            context_str += f"- {mid} (score {score:.2f})\n"
    else:
        context_str += "No relevant memories.\n"

    if knowledge:
        context_str += "\nRelevant knowledge:\n"
        for kid, score in knowledge:
            context_str += f"- {kid} (score {score:.2f})\n"
    else:
        context_str += "\nNo relevant knowledge.\n"

    prompt = f"""
        You are the AI's internal reasoning module.

        User query:
        {query}

        Workspace context:
        {context_str}

        Generate a short internal reasoning step (not to be shown to user).
        Focus only on relevant items. If none are relevant, reason from general principles.
        """

    return llm(prompt)

def autonomous_memory_cycle(min_strength=0.75):
    """
    Converts strong thoughts into episodic memories automatically.
    Also decays weaker thoughts.
    """
    import time

    path = "thought_store/thoughts.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            thoughts = json.load(f)
    except:
        thoughts = []

    new_thoughts = []
    for t in thoughts:
        age_hours = (time.time() - t["timestamp"]) / 3600
        strength = t["strength"] * (1 - t["decay_rate"]) ** age_hours

        # Convert strong thoughts to memories
        if strength >= min_strength:
            create_new_memory_from_thought(t["content"])

        # Keep surviving thoughts
        if strength > 0.15:
            t["strength"] = strength
            new_thoughts.append(t)

    # Save updated thought store
    with open(path, "w", encoding="utf-8") as f:
        json.dump(new_thoughts, f, indent=2)

def autonomous_mind_loop(interval_seconds=30):
    """
    Runs the AI's autonomous mind indefinitely.
    Generates thoughts and consolidates memories periodically.
    """
    def loop():
        while True:
            try:
                autonomous_thought_cycle()    # generate new thoughts
                autonomous_memory_cycle()     # consolidate strong thoughts
            except Exception as e:
                print("[Autonomous Mind Error]", e)
            time.sleep(interval_seconds)

    # Run loop in a separate thread
    t = threading.Thread(target=loop, daemon=True)
    t.start()
    print(f"[Autonomous Mind] Started with interval {interval_seconds} seconds.")

def autonomous_thought_cycle(max_memories=5, max_knowledge=5, default_strength=0.4):
    """
    Generates an internal thought autonomously using memories and knowledge.
    Stores it in WORKING state and thought_store.
    """
    global WORKING, memory_index, knowledge_index

    # --- Gather memory context ---
    if memory_index:
        # Pick recent/high relevance memories
        recent_memories = sorted(memory_index.items(), key=lambda x: x[1]['last_accessed'], reverse=True)
        memory_texts = [f"{m['title']}: {m.get('dominant_emotion', 'Neutral')}" for _, m in recent_memories[:max_memories]]
    else:
        memory_texts = []

    # --- Gather knowledge context ---
    knowledge_texts = [k['content'] for k in list(knowledge_index.values())[:max_knowledge]]

    # --- Prepare prompt for internal reflection ---
    prompt = "You are an AI reflecting silently. Generate a short internal thought based on the following:\n\n"
    if memory_texts:
        prompt += "Memories:\n" + "\n".join(memory_texts) + "\n\n"
    if knowledge_texts:
        prompt += "Knowledge:\n" + "\n".join(knowledge_texts) + "\n\n"
    prompt += "Generate a single actionable or reflective internal thought (1-2 sentences)."

    # --- Call LLM to generate thought ---
    thought_text = llm(prompt)

    # --- Store thought ---
    store_working_thought(thought_text, default_strength)
    add_thought(thought_text, type="autonomous", importance=default_strength)

def autonomous_realtime_loop(poll_interval=5):
    """
    Continuously monitor camera and microphone for new users.
    Creates or updates memory, thought, and knowledge automatically.
    """
    print("[Autonomous Loop] Starting real-time user monitoring...")
    
    while True:
        try:
            # Capture a short segment of video+audio
            face_enc, audio_file, video_file = capture_user_audio_video(duration=3)

            if face_enc is None:
                time.sleep(poll_interval)
                continue

            # Check if user exists
            mem_id, user_name = recognize_user(face_enc)

            if mem_id:
                # Existing user → update last_accessed
                memory_index[mem_id]["last_accessed"] = time.time()
                thought_content = f"Returning user '{user_name}' interacted again. Memory ID: {mem_id}."
                add_thought(thought_content, type="user_interaction", importance=0.5)
                print(f"[User Recognized] {user_name} (Memory: {mem_id})")
            else:
                # New user → automatically assign a temporary name
                user_name = f"User_{int(time.time())}"
                store_user_profile(face_enc, audio_file, video_file, user_name)
                mem_id = f"M{int(time.time())}"

                thought_content = f"New user '{user_name}' detected and stored. Memory ID: {mem_id}."
                add_thought(thought_content, type="user_interaction", importance=0.7)
                print(f"[New User] {user_name} stored in memory.")

            # Optional: generate internal reasoning for this interaction
            query = f"Analyze user '{user_name}' interaction for emotional creativity and generate insights."
            workspace = build_workspace(query)
            print("[Autonomous LLM Thought]")
            print(workspace["internal_thoughts"])

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\n[Autonomous Loop] Stopped by user.")
            break
        except Exception as e:
            print(f"[Autonomous Loop] Error: {e}")
            time.sleep(poll_interval)

# ======================================================================================

# Start the AI's self-thinking process
autonomous_realtime_loop()  # generates + consolidates every 60s

'''
query = "How can I improve Haruka’s emotional creativity module?"
#context = generate_context(query) # For Memory
llm_input = build_workspace(query) # For Thoughts
add_thought("User asked: " + query, type="query", importance=0.4)
debug_show_recent_thoughts() # For Thoughts

# llm_input = f"Relevant memories:\n{context}\n\nUser query:\n{query}\n\nRespond using insights above."
print(llm_input)
'''

# time.sleep(30)
# decay_and_consolidate_thoughts()
