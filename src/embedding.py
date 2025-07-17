import os
import json
import faiss
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

PROCESSED_FOLDER = "data/processed/"
VECTOR_STORE_FOLDER = "data/vector_store/"
EMBEDDING_MODEL = "bkai-foundation-models/vietnamese-bi-encoder"

class VietnameseBiEncoder:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def encode(self, texts, batch_size=16):
        self.model.eval()
        embeddings = []

        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                encoded_input = self.tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors="pt")
                model_output = self.model(**encoded_input)
                attention_mask = encoded_input['attention_mask']
                last_hidden = model_output.last_hidden_state
                mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
                sum_embeddings = torch.sum(last_hidden * mask_expanded, 1)
                sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
                batch_embeds = (sum_embeddings / sum_mask).cpu().numpy()
                embeddings.extend(batch_embeds)

        return np.array(embeddings)

def load_chunks_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)
def build_vector_store(processed_folder, vector_store_folder, embedding_model):
    model = VietnameseBiEncoder(embedding_model)
    all_texts = []
    all_metas = []

    for fname in os.listdir(processed_folder):
        # BỎ QUA file social_responses.json
        if fname == "social_responses.json":
            continue
        if fname.endswith(".json"):
            file_path = os.path.join(processed_folder, fname)
            chunks = load_chunks_from_json(file_path)
            for chunk in chunks:
                if "text" not in chunk or "metadata" not in chunk:
                    print(f"Lỗi: chunk bị thiếu 'text' hoặc 'metadata': {chunk}")
                    continue  # bỏ qua chunk lỗi
                all_texts.append(chunk["text"])
                all_metas.append(chunk["metadata"])

    if all_texts:
        embeddings = model.encode(all_texts)
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
