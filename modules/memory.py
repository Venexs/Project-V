"""Memory management with automatic indexing and embedding generation"""
import os
import json
import time
import numpy as np
from sentence_transformers import SentenceTransformer, util
import torch
from datetime import datetime
from typing import List, Tuple, Dict, Optional

# Load embedding model
with open("config.json", "r") as f:
    MODEL_NAME = json.load(f)["embedding_model"]
model = SentenceTransformer(MODEL_NAME)

MEMORY_DIR = "memories"
MEMORY_INDEX_FILE = "memory_index.json"
SEMANTIC_INDEX_FILE = "semantic_index.npy"
GRAPH_FILE = "graph.json"
# Global list to track recently retrieved memories (Short Term Memory Buffer)
RECENT_RETRIEVALS = [] 

def safe_list(value):
    """Ensure value is a list"""
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []

def create_memory(content: str, title: str = None, people: List[str] = None, 
                  topics: List[str] = None, objects: List[str] = None,
                  emotion: Dict[str, float] = None,
                  face_encoding: Optional[np.ndarray] = None,
                  audio_file: str = None, video_file: str = None) -> str:
    """
    Create a new memory and automatically update indices.
    emotion: 6D emotion graph dict with keys: Happy, Sad, Anger, Fear, Disgust, Surprise
    Returns memory_id
    """
    from modules.emotions import get_default_emotion, create_emotion_graph
    
    mem_id = f"M{int(time.time() * 1000)}"
    mem_path = os.path.join(MEMORY_DIR, mem_id)
    os.makedirs(mem_path, exist_ok=True)
    
    # Save text content
    with open(os.path.join(mem_path, "text.txt"), "w", encoding="utf-8") as f:
        f.write(content)
    
    # Normalize emotion to 6D graph
    if emotion is None:
        emotion = get_default_emotion()
    else:
        emotion = create_emotion_graph(
            happy=emotion.get("Happy", 0.0),
            sad=emotion.get("Sad", 0.0),
            anger=emotion.get("Anger", 0.0),
            fear=emotion.get("Fear", 0.0),
            disgust=emotion.get("Disgust", 0.0),
            surprise=emotion.get("Surprise", 0.0)
        )
    
    # Get dominant emotion and intensity for backward compatibility
    from modules.emotions import get_dominant_emotion, get_emotion_intensity
    dominant_emotion = get_dominant_emotion(emotion)
    emotion_intensity = get_emotion_intensity(emotion)
    
    # Create metadata
    meta = {
        "title": title or f"Memory {mem_id}",
        "summary": content[:200] + "..." if len(content) > 200 else content,
        "people": safe_list(people or []),
        "objects": safe_list(objects or []),
        "topics": safe_list(topics or []),
        "emotion": emotion,  # 6D emotion graph
        "dominant_emotion": dominant_emotion,  # For backward compatibility
        "emotion_intensity": float(emotion_intensity),  # For backward compatibility
        "last_accessed": time.time(),
        "tag_relevance": 1.0
    }
    
    if face_encoding is not None:
        meta["face_encoding"] = face_encoding.tolist()
    if audio_file:
        meta["audio_file"] = audio_file
    if video_file:
        meta["video_file"] = video_file
    
    # Save metadata
    with open(os.path.join(mem_path, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    # Auto-regenerate indices
    rebuild_memory_index()
    rebuild_semantic_index()
    rebuild_memory_graph()
    
    print(f"[Memory] Created {mem_id}: {meta['title']}")
    return mem_id

def rebuild_memory_index():
    """Rebuild memory_index.json from all memory folders"""
    memory_index = {}
    
    if not os.path.exists(MEMORY_DIR):
        os.makedirs(MEMORY_DIR, exist_ok=True)
        with open(MEMORY_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        return {}
    
    for folder in sorted(os.listdir(MEMORY_DIR)):
        folder_path = os.path.join(MEMORY_DIR, folder)
        meta_path = os.path.join(folder_path, "meta.json")
        
        if not os.path.isdir(folder_path) or not os.path.exists(meta_path):
            continue
        
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            
            # Load emotion - support both old and new format
            from modules.emotions import get_default_emotion, create_emotion_graph, get_dominant_emotion, get_emotion_intensity
            
            emotion = meta.get("emotion")
            if emotion is None:
                # Old format - convert to 6D graph
                dominant = meta.get("dominant_emotion", "Neutral")
                intensity = float(meta.get("emotion_intensity", 0.5))
                emotion = get_default_emotion()
                if dominant != "Neutral" and intensity > 0:
                    # Map old emotion names to new axes
                    emotion_map = {
                        "Happy": "Happy",
                        "Sad": "Sad",
                        "Angry": "Anger",
                        "Anger": "Anger",
                        "Fear": "Fear",
                        "Disgust": "Disgust",
                        "Surprise": "Surprise",
                        "Curious": "Surprise",
                        "Neutral": None
                    }
                    axis = emotion_map.get(dominant)
                    if axis:
                        emotion[axis] = intensity
                # Convert emotion dict keys to lowercase for create_emotion_graph
                emotion = create_emotion_graph(
                    happy=emotion.get("Happy", 0.0),
                    sad=emotion.get("Sad", 0.0),
                    anger=emotion.get("Anger", 0.0),
                    fear=emotion.get("Fear", 0.0),
                    disgust=emotion.get("Disgust", 0.0),
                    surprise=emotion.get("Surprise", 0.0)
                )
            
            memory_index[folder] = {
                "title": meta.get("title", f"Memory {folder}"),
                "people": safe_list(meta.get("people", [])),
                "objects": safe_list(meta.get("objects", [])),
                "topics": safe_list(meta.get("topics", [])),
                "emotion": emotion,  # 6D emotion graph
                "dominant_emotion": get_dominant_emotion(emotion),  # For backward compatibility
                "emotion_intensity": float(get_emotion_intensity(emotion)),  # For backward compatibility
                "last_accessed": float(meta.get("last_accessed", time.time())),
                "tag_relevance": float(meta.get("tag_relevance", 1.0)),
                "face_encoding": meta.get("face_encoding"),
                "audio_file": meta.get("audio_file"),
                "video_file": meta.get("video_file")
            }
        except Exception as e:
            print(f"[WARN] Failed to process {folder}: {e}")
            continue
    
    with open(MEMORY_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(memory_index, f, indent=2, ensure_ascii=False)
    
    return memory_index

def rebuild_semantic_index():
    """Rebuild semantic_index.npy from memory text files"""
    semantic_vectors = {}
    
    if not os.path.exists(MEMORY_DIR):
        np.save(SEMANTIC_INDEX_FILE, semantic_vectors)
        return {}
    
    for folder in os.listdir(MEMORY_DIR):
        text_path = os.path.join(MEMORY_DIR, folder, "text.txt")
        if not os.path.exists(text_path):
            continue
        
        try:
            with open(text_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            if text.strip():
                vector = model.encode(text, normalize_embeddings=True)
                semantic_vectors[folder] = vector
        except Exception as e:
            print(f"[WARN] Failed to encode {folder}: {e}")
            continue
    
    np.save(SEMANTIC_INDEX_FILE, semantic_vectors)
    return semantic_vectors

def rebuild_memory_graph():
    """Rebuild graph.json from memory index"""
    if not os.path.exists(MEMORY_INDEX_FILE):
        with open(GRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        return {}
    
    with open(MEMORY_INDEX_FILE, "r", encoding="utf-8") as f:
        index = json.load(f)
    
    if len(index) < 2:
        with open(GRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        return {}
    
    # Prepare semantic text
    texts = {}
    for mid, meta in index.items():
        title = meta.get("title", "")
        topics = " ".join(meta.get("topics", []))
        people = " ".join(meta.get("people", []))
        combined = f"{title} {topics} {people}"
        texts[mid] = combined.strip() or "empty memory"
    
    # Reuse cached semantic embeddings if available to avoid re-encoding every memory
    memory_ids = list(texts.keys())
    semantic_index = load_semantic_index()
    embeddings_list = []
    missing_ids = []
    missing_texts = []

    for mid in memory_ids:
        if mid in semantic_index:
            embeddings_list.append(semantic_index[mid])
        else:
            missing_ids.append(mid)
            missing_texts.append(texts[mid])

    if missing_texts:
        new_vecs = model.encode(missing_texts, normalize_embeddings=True)
        for mid, vec in zip(missing_ids, new_vecs):
            semantic_index[mid] = vec
            embeddings_list.append(vec)
        np.save(SEMANTIC_INDEX_FILE, semantic_index)

    embeddings = np.array(embeddings_list)
    
    # Build graph
    graph = {}
    SIM_THRESHOLD = 0.25
    
    import itertools
    for id1, id2 in itertools.combinations(index.keys(), 2):
        m1, m2 = index[id1], index[id2]
        
        # Tag-based weights
        shared_people = set(m1.get("people", [])) & set(m2.get("people", []))
        shared_topics = set(m1.get("topics", [])) & set(m2.get("topics", []))
        shared_objs = set(m1.get("objects", [])) & set(m2.get("objects", []))
        
        weight = 0.0
        reason = []
        if shared_people:
            weight += 0.5
            reason.append(f"shared_person_{list(shared_people)[0]}")
        if shared_topics:
            weight += 0.3
            reason.append(f"shared_topic_{list(shared_topics)[0]}")
        if shared_objs:
            weight += 0.2
            reason.append(f"shared_object_{list(shared_objs)[0]}")
        
        # Semantic similarity
        vec1 = embeddings[memory_ids.index(id1)]
        vec2 = embeddings[memory_ids.index(id2)]
        sim = float(util.cos_sim(torch.tensor(vec1), torch.tensor(vec2)))
        
        if sim >= SIM_THRESHOLD:
            weight += sim * 0.4
            reason.append(f"semantic_similarity_{sim:.2f}")
        
        if weight > 0:
            graph.setdefault(id1, []).append({
                "target": id2,
                "weight": round(weight, 3),
                "reason": ",".join(reason)
            })
            graph.setdefault(id2, []).append({
                "target": id1,
                "weight": round(weight, 3),
                "reason": ",".join(reason)
            })
    
    with open(GRAPH_FILE, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
    
    return graph

def load_memory_index() -> Dict:
    """Load memory index"""
    if not os.path.exists(MEMORY_INDEX_FILE):
        return {}
    with open(MEMORY_INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_semantic_index() -> Dict:
    """Load semantic index"""
    if not os.path.exists(SEMANTIC_INDEX_FILE):
        return {}
    return np.load(SEMANTIC_INDEX_FILE, allow_pickle=True).item()

def load_memory_graph() -> Dict:
    """Load memory graph"""
    if not os.path.exists(GRAPH_FILE):
        return {}
    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def retrieve_similar_memories(query: str, top_k: int = 3) -> List[Tuple[str, float]]:
    """Retrieve similar memories using semantic search"""
    memory_index = load_memory_index()
    if not memory_index:
        return []
    
    memory_ids = list(memory_index.keys())
    memory_texts = []
    
    for mid in memory_ids:
        meta = memory_index[mid]
        summary = meta.get("title", "") + ". " + ", ".join(meta.get("topics", []))
        memory_texts.append(summary)
    
    mem_embeddings = model.encode(memory_texts, convert_to_tensor=True)
    q_embedding = model.encode(query, convert_to_tensor=True)
    
    if mem_embeddings.device != q_embedding.device:
        q_embedding = q_embedding.to(mem_embeddings.device)
    
    scores = util.cos_sim(q_embedding, mem_embeddings)[0]
    top = torch.topk(scores, k=min(top_k, len(memory_texts)))
    
    results = [(memory_ids[i], float(scores[i])) for i in top.indices]
    return results

def compute_activation(memory_id: str, similarity: float, memory_index: Dict, suppression_ids: List[str] = None) -> float:
    """
    Compute activation score with IMPROVED Repetition Penalty.
    """
    from modules.emotions import get_emotion_intensity
    
    if suppression_ids is None:
        suppression_ids = []

    meta = memory_index.get(memory_id, {})
    
    # Recency with steeper decay
    recency_days = (time.time() - meta.get("last_accessed", 0)) / 86400
    recency_factor = np.exp(-recency_days / 2.0) 
    
    # Get emotion intensity
    emotion = meta.get("emotion")
    if emotion:
        emotion_factor = get_emotion_intensity(emotion)
    else:
        emotion_factor = float(meta.get("emotion_intensity", 0.5))
    
    tag_weight = meta.get("tag_relevance", 1.0)
    
    # Calculate Base Score - INCREASED similarity weight
    score = (
        similarity * 0.65       # Increased from 0.5 - semantic match is important!
        + tag_weight * 0.15     # Reduced from 0.2
        + recency_factor * 0.15 # Reduced from 0.2
        + emotion_factor * 0.05 # Reduced from 0.1
    )

    # IMPROVED Repetition Penalty - less aggressive
    # Only suppress if seen VERY recently (last 2 retrievals, not last 5)
    if memory_id in suppression_ids[-2:]:  # Only last 2, not all 5
        score = score * 0.5  # 50% penalty instead of 80%
        
    return score

def expand_graph_nodes(memory_id: str, memory_graph: Dict, depth: int = 1) -> List[Tuple[str, float]]:
    """Expand graph nodes to find related memories"""
    related = []
    frontier = [memory_id]
    
    for _ in range(depth):
        new_frontier = []
        for node in frontier:
            edges = memory_graph.get(node, [])
            for edge in edges:
                target = edge["target"]
                weight = edge["weight"]
                if weight > 0.7:
                    related.append((target, weight))
                    new_frontier.append(target)
        frontier = new_frontier
    
    return related

def associative_recall(query: str, top_k: int = 3) -> List[Tuple[str, float]]:
    """Associative memory recall with IMPROVED inhibition of return"""
    global RECENT_RETRIEVALS
    
    # 1. Retrieve MORE candidates initially
    candidates = retrieve_similar_memories(query, top_k=15)  # Increased from 10
    memory_index = load_memory_index()
    memory_graph = load_memory_graph()
    activated = {}
    
    # 2. Compute activation with LESS aggressive suppression
    for mem_id, sim in candidates:
        # Only pass last 2 recent retrievals for suppression
        recent_for_suppression = RECENT_RETRIEVALS[-2:] if len(RECENT_RETRIEVALS) >= 2 else RECENT_RETRIEVALS
        act = compute_activation(mem_id, sim, memory_index, suppression_ids=recent_for_suppression)
        activated[mem_id] = act
        
        # Graph traversal - LESS aggressive decay
        for related_id, w in expand_graph_nodes(mem_id, memory_graph, depth=1):
            act_related = act * w * 0.9  # Increased from 0.8 - less decay
            
            # Only suppress related if seen in last 2 retrievals
            if related_id in RECENT_RETRIEVALS[-2:]:
                act_related *= 0.5  # 50% penalty instead of 80%
                
            activated[related_id] = max(activated.get(related_id, 0), act_related)
    
    # 3. Rank and Select
    ranked = sorted(activated.items(), key=lambda x: x[1], reverse=True)
    selected_memories = ranked[:top_k]
    
    # 4. Update Short Term Memory Buffer - Keep last 3 instead of 5
    current_ids = [m[0] for m in selected_memories]
    RECENT_RETRIEVALS.extend(current_ids)
    if len(RECENT_RETRIEVALS) > 3:  # Reduced from 5
        RECENT_RETRIEVALS = RECENT_RETRIEVALS[-3:]
        
    return selected_memories

