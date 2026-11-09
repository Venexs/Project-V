from sentence_transformers import SentenceTransformer
import numpy as np, os, json

with open("config.json") as f:
    MODEL_NAME = json.load(f)["embedding_model"]
model = SentenceTransformer(MODEL_NAME)

semantic_vectors = {}

for folder in os.listdir("memories"):
    text_path = f"memories/{folder}/text.txt"
    if not os.path.exists(text_path): continue

    with open(text_path, "r") as f:
        text = f.read()

    vector = model.encode(text)
    semantic_vectors[folder] = vector

np.save("semantic_index.npy", semantic_vectors)
