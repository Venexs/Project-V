# build_knowledge_embeddings.py
import json, numpy as np

def embed(text):
    # placeholder embedding
    return np.random.rand(384)

with open("knowledge_index.json", "r") as f:
    index = json.load(f)

embeddings = {}

for kid, meta in index.items():
    combined_text = meta["title"] + " " + " ".join(meta["keywords"]) + " " + meta["summary"]
    embeddings[kid] = embed(combined_text)

np.save("knowledge_embeddings.npy", embeddings)

print("Knowledge embeddings created.")
