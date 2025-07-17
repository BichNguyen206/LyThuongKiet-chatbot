import os
import json
import faiss
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

# --------- CẤU HÌNH ---------
SOCIAL_RESPONSES_PATH = "data/processed/social_responses.json"
VECTOR_STORE_PATH = "data/social_vector_store"
MODEL_NAME = "bkai-foundation-models/vietnamese-bi-encoder"

# --------- LOAD MÔ HÌNH ---------
class VietnameseBiEncoder:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    def encode(self, texts, batch_size=16):
        embeddings = []
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                encoded = self.tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors="pt")
                attention_mask = encoded['attention_mask']
                output = self.model(**encoded)
                last_hidden = output.last_hidden_state
                mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
                sum_embeddings = torch.sum(last_hidden * mask_expanded, 1)
                sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
                batch_embeds = (sum_embeddings / sum_mask).cpu().numpy()
                embeddings.extend(batch_embeds)
        return np.array(embeddings)

# --------- LOAD DỮ LIỆU ---------
def load_social_pairs(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --------- MAIN ---------
def build_social_vector_store():
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    encoder = VietnameseBiEncoder(MODEL_NAME)

    # Đọc danh sách [{question: ..., response: ...}]
    with open(SOCIAL_RESPONSES_PATH, "r", encoding="utf-8") as f:
        social_data = json.load(f)

    questions = [item["question"] for item in social_data]
    answer = [item["answer"] for item in social_data]

    embeddings = encoder.encode(questions)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Lưu FAISS index
    faiss.write_index(index, os.path.join(VECTOR_STORE_PATH, "social.index"))

    # Lưu metadata
    with open(os.path.join(VECTOR_STORE_PATH, "social_meta.json"), "w", encoding="utf-8") as f:
        json.dump({"questions": questions, "answer": answer}, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã tạo social vector store với {len(questions)} câu xã giao.")

if __name__ == "__main__":
    build_social_vector_store()
