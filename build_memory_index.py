import os
import json
import time

MEMORY_DIR = "memories"
OUTPUT_FILE = "memory_index.json"

memory_index = {}

# loop through all subfolders inside /memories
for folder in sorted(os.listdir(MEMORY_DIR)):
    folder_path = os.path.join(MEMORY_DIR, folder)
    meta_path = os.path.join(folder_path, "meta.json")

    # skip anything that's not a folder or doesn't have meta.json
    if not os.path.isdir(folder_path) or not os.path.exists(meta_path):
        continue

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        # validate types — ensure lists, not strings or nulls
        def safe_list(value):
            if isinstance(value, list):
                return value
            if isinstance(value, str) and value.strip():
                return [value.strip()]
            return []

        # build normalized entry
        memory_index[folder] = {
            "title": meta.get("title", f"Memory {folder}"),
            "people": safe_list(meta.get("people", [])),
            "objects": safe_list(meta.get("objects", [])),
            "topics": safe_list(meta.get("topics", [])),
            "dominant_emotion": meta.get("dominant_emotion", "Neutral"),
            "emotion_intensity": float(meta.get("emotion_intensity", 0.5)),
            "last_accessed": float(meta.get("last_accessed", time.time())),
            "tag_relevance": float(meta.get("tag_relevance", 1.0))
        }

    except Exception as e:
        print(f"[WARN] Failed to process {folder}: {e}")
        continue

# write to file safely
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(memory_index, f, indent=2, ensure_ascii=False)

print(f"[OK] Indexed {len(memory_index)} memories → {OUTPUT_FILE}")


# run in order:

#python build_memory_index.py
#python build_semantic_index.py
#python build_memory_graph.py
