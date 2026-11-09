import itertools, json, time
import numpy as np
from sentence_transformers import SentenceTransformer, util

# ===== Load memory index =====
with open("memory_index.json") as f:
    index = json.load(f)

# ===== Initialize semantic model =====
with open("config.json") as f:
    MODEL_NAME = json.load(f)["embedding_model"]
model = SentenceTransformer(MODEL_NAME)

# ===== Prepare semantic text for each memory =====
texts = {}
for mid, meta in index.items():
    title = meta.get("title", "")
    topics = " ".join(meta.get("topics", []))
    people = " ".join(meta.get("people", []))
    combined = f"{title} {topics} {people}"
    texts[mid] = combined.strip() or "empty memory"

# ===== Encode all memories =====
memory_ids = list(texts.keys())
embeddings = model.encode(list(texts.values()), normalize_embeddings=True)
embeddings = np.array(embeddings)

# ===== Build graph =====
graph = {}
SIM_THRESHOLD = 0.25  # looser threshold so we get links
DEBUG = True


for id1, id2 in itertools.combinations(index.keys(), 2):
    m1, m2 = index[id1], index[id2]

    # basic tag-based weights
    shared_people = set(m1.get("people", [])) & set(m2.get("people", []))
    shared_topics = set(m1.get("topics", [])) & set(m2.get("topics", []))
    shared_objs   = set(m1.get("objects", [])) & set(m2.get("objects", []))

    weight = 0.0
    reason = []
    if shared_people:
        weight += 0.5; reason.append(f"shared_person_{list(shared_people)[0]}")
    if shared_topics:
        weight += 0.3; reason.append(f"shared_topic_{list(shared_topics)[0]}")
    if shared_objs:
        weight += 0.2; reason.append(f"shared_object_{list(shared_objs)[0]}")

    # ===== Add semantic similarity =====
    vec1 = embeddings[memory_ids.index(id1)]
    vec2 = embeddings[memory_ids.index(id2)]
    sim = float(util.cos_sim(vec1, vec2))
    
    if sim >= SIM_THRESHOLD:
        weight += sim * 0.4  # weight semantic connection lightly
        reason.append(f"semantic_similarity_{sim:.2f}")

    if DEBUG:
        print(f"{id1} ↔ {id2} = {sim:.3f}")


    # ===== Only keep edges above minimal weight =====
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

# ===== Save graph =====
with open("graph.json", "w") as f:
    json.dump(graph, f, indent=2)

print(f"✅ Graph built with {len(graph)} nodes and semantic associations.")
