"""Knowledge management with automatic indexing and embedding generation"""
import os
import json
import time
import numpy as np
from sentence_transformers import SentenceTransformer, util
import torch
from typing import List, Tuple, Dict, Optional

# Load embedding model
with open("config.json", "r") as f:
    MODEL_NAME = json.load(f)["embedding_model"]
model = SentenceTransformer(MODEL_NAME)

KNOWLEDGE_DIR = "knowledge_store"
KNOWLEDGE_INDEX_FILE = "knowledge_index.json"
KNOWLEDGE_EMBEDDINGS_FILE = "knowledge_embeddings.npy"

def create_knowledge(title: str, content: str, keywords: List[str] = None,
                    summary: str = None, importance: float = 0.5) -> str:
    """
    Create a new knowledge item and automatically update indices.
    Returns knowledge_id
    """
    # Ensure keywords is always a list
    if keywords is None:
        keywords = []
    elif not isinstance(keywords, list):
        # If it's not a list, try to convert it
        if isinstance(keywords, str):
            keywords = [keywords]
        else:
            keywords = []
    
    kid = f"K{int(time.time() * 1000)}"
    knowledge_path = os.path.join(KNOWLEDGE_DIR, kid)
    os.makedirs(knowledge_path, exist_ok=True)
    
    meta = {
        "title": title,
        "content": content,
        "summary": summary or content[:200] + "..." if len(content) > 200 else content,
        "tags": keywords,  # Now guaranteed to be a list
        "importance": float(importance),
        "last_updated": time.time()
    }
    
    with open(os.path.join(knowledge_path, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    # Auto-regenerate indices
    rebuild_knowledge_index()
    rebuild_knowledge_embeddings()
    
    print(f"[Knowledge] Created {kid}: {title}")
    return kid

def rebuild_knowledge_index():
    """Rebuild knowledge_index.json from all knowledge folders"""
    knowledge_index = {}
    
    if not os.path.exists(KNOWLEDGE_DIR):
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
        with open(KNOWLEDGE_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        return {}
    
    for folder in os.listdir(KNOWLEDGE_DIR):
        meta_path = os.path.join(KNOWLEDGE_DIR, folder, "meta.json")
        if not os.path.exists(meta_path):
            continue
        
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            
            knowledge_index[folder] = {
                "title": meta.get("title", folder),
                "keywords": meta.get("tags", []),
                "summary": meta.get("summary", "No summary available."),
                "content": meta.get("content", meta.get("summary", "No summary available.")),
                "importance": meta.get("importance", 0.5),
                "last_updated": meta.get("last_updated", time.time())
            }
        except Exception as e:
            print(f"[WARN] Failed to process {folder}: {e}")
            continue
    
    with open(KNOWLEDGE_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(knowledge_index, f, indent=2, ensure_ascii=False)
    
    return knowledge_index

def rebuild_knowledge_embeddings():
    """Rebuild knowledge_embeddings.npy from knowledge index"""
    if not os.path.exists(KNOWLEDGE_INDEX_FILE):
        np.save(KNOWLEDGE_EMBEDDINGS_FILE, {})
        return {}
    
    with open(KNOWLEDGE_INDEX_FILE, "r", encoding="utf-8") as f:
        index = json.load(f)
    
    embeddings = {}
    
    for kid, meta in index.items():
        combined_text = meta["title"] + " " + " ".join(meta.get("keywords", [])) + " " + meta.get("summary", "")
        if combined_text.strip():
            embedding = model.encode(combined_text, normalize_embeddings=True)
            embeddings[kid] = embedding
    
    np.save(KNOWLEDGE_EMBEDDINGS_FILE, embeddings)
    return embeddings

def load_knowledge_index() -> Dict:
    """Load knowledge index"""
    if not os.path.exists(KNOWLEDGE_INDEX_FILE):
        return {}
    with open(KNOWLEDGE_INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_knowledge_embeddings() -> Dict:
    """Load knowledge embeddings"""
    if not os.path.exists(KNOWLEDGE_EMBEDDINGS_FILE):
        return {}
    return np.load(KNOWLEDGE_EMBEDDINGS_FILE, allow_pickle=True).item()

def retrieve_knowledge(query: str, top_k: int = 3) -> List[Tuple[str, float]]:
    """Retrieve similar knowledge using semantic search"""
    knowledge_index = load_knowledge_index()
    if not knowledge_index:
        return []
    
    knowledge_ids = list(knowledge_index.keys())
    knowledge_texts = [knowledge_index[k]["content"] for k in knowledge_ids]
    
    emb_tensor = model.encode(knowledge_texts, convert_to_tensor=True)
    q_emb = model.encode(query, convert_to_tensor=True)
    
    if emb_tensor.device != q_emb.device:
        q_emb = q_emb.to(emb_tensor.device)
    if emb_tensor.dtype != q_emb.dtype:
        q_emb = q_emb.to(emb_tensor.dtype)
    
    scores = util.cos_sim(q_emb, emb_tensor)[0]
    top = torch.topk(scores, k=min(top_k, len(knowledge_texts)))
    
    results = [(knowledge_ids[i], float(scores[i])) for i in top.indices]
    return results

