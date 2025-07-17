import re
import json
import os
from collections import deque
from datetime import datetime
from functools import lru_cache
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from pyvi import ViTokenizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------- Mô hình BkAI ----------
class VietnameseBiEncoder:
    def __init__(self, model_name="bkai-foundation-models/vietnamese-bi-encoder"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    def encode(self, texts, batch_size=8):
        embeddings = []
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                batch = [ViTokenizer.tokenize(t) for t in batch]
                encoded_input = self.tokenizer(batch, padding=True, truncation=True, return_tensors="pt", max_length=128)
                model_output = self.model(**encoded_input)
                attention_mask = encoded_input['attention_mask']
                last_hidden = model_output.last_hidden_state
                mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
                sum_embeddings = torch.sum(last_hidden * mask_expanded, 1)
                sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
                batch_embeddings = (sum_embeddings / sum_mask).cpu().numpy()
                embeddings.extend(batch_embeddings)
        return np.array(embeddings)

bi_encoder = VietnameseBiEncoder()

# ---------- Luật thay thế ----------
HARD_REPLACEMENTS = {
    "cho em hỏi": "",
    "thầy cô ơi": "",
    "xin hỏi": "",
    "vậy ạ": "",
    "ạ": "",
    "cho mình hỏi": "",
    "ad ơi": "",
    "chị ơi": "",
    "anh ơi": "",
    "tkb": "thời khóa biểu",
    "gv": "giáo viên",
    "ppct": "phân phối chương trình",
    "ntn": "như thế nào"
}

# ---------- Làm sạch ----------
def clean_text(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

# ---------- Log theo lô ----------
log_queue = deque()
def flush_logs():
    if not log_queue:
        return
    os.makedirs("data/logs", exist_ok=True)
    with open("data/logs/question_normalization_log.jsonl", "a", encoding="utf-8") as f:
        while log_queue:
            f.write(json.dumps(log_queue.popleft(), ensure_ascii=False) + "\n")

# ---------- Chuẩn hóa ----------
@lru_cache(maxsize=1000)
def normalize_question(text, threshold=0.75, use_gpt=False):
    original = text
    text = clean_text(text)

    for src, tgt in HARD_REPLACEMENTS.items():
        if src in text:
            text = text.replace(src, tgt).strip()

    # Ghi log vào queue
    log_queue.append({
        "timestamp": str(datetime.now()),
        "user_question": original,
        "normalized": text
    })

    # Flush log nếu nhiều hơn 10 dòng
    #if len(log_queue) >= 10:
    flush_logs()

    return text