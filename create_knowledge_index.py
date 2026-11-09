# create_knowledge_index.py
import os, json, time

knowledge_index = {}

for folder in os.listdir("knowledge_store"):
    meta_path = f"knowledge_store/{folder}/meta.json"
    if not os.path.exists(meta_path):
        continue

    with open(meta_path, "r") as f:
        meta = json.load(f)

    knowledge_index[folder] = {
        "title": meta.get("title", folder),
        "keywords": meta.get("tags", []),
        "summary": meta.get("summary", "No summary available."),
        "content": meta.get("content", meta.get("summary", "No summary available.")),  # ✅ FIX
        "importance": meta.get("importance", 0.5),
        "last_updated": time.time(),
    }

with open("knowledge_index.json", "w") as f:
    json.dump(knowledge_index, f, indent=2)

print("Knowledge index built.")
