import os
import json
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np

PROCESSED_FOLDER = "data/processed/"
VECTOR_STORE_FOLDER = "data/vector_store/"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def load_chunks_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_vector_store(processed_folder, vector_store_folder, embedding_model):
    model = SentenceTransformer(embedding_model)
    all_texts = []
    all_metas = []

    for fname in os.listdir(processed_folder):
        if fname.endswith(".json"):
            file_path = os.path.join(processed_folder, fname)
            chunks = load_chunks_from_json(file_path)
            all_texts.extend([chunk["text"] for chunk in chunks])
            all_metas.extend([chunk["metadata"] for chunk in chunks])

    if all_texts:
        # Nhúng toàn bộ văn bản thành vector
        embeddings = model.encode(all_texts, show_progress_bar=True, convert_to_numpy=True)
        # Xây FAISS index
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)
        os.makedirs(vector_store_folder, exist_ok=True)
        faiss.write_index(index, os.path.join(vector_store_folder, "vector_db.index"))
        with open(os.path.join(vector_store_folder, "vector_db_meta.json"), "w", encoding="utf-8") as f:
            json.dump({"metadatas": all_metas, "texts": all_texts}, f, ensure_ascii=False, indent=2)
        print(f"Saved vector store (FAISS) with {len(all_texts)} chunks to {vector_store_folder}")

    else:
        print("No data to embed!")
if __name__ == "__main__":
    build_vector_store(PROCESSED_FOLDER, VECTOR_STORE_FOLDER, EMBEDDING_MODEL)
