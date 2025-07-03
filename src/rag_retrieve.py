import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import json
import openai
import os
from dotenv import load_dotenv
from cache import find_in_history, find_in_history_fuzzy, save_history

# --------- Load dữ liệu và model chỉ 1 lần khi app start ---------
VECTOR_STORE_PATH = "data/vector_store/vector_db.index"
META_PATH = "data/vector_store/vector_db_meta.json"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# 1. Load FAISS index
index = faiss.read_index(VECTOR_STORE_PATH)

# 2. Load meta & texts
with open(META_PATH, "r", encoding="utf-8") as f:
    meta = json.load(f)
    all_texts = meta["texts"]
    all_metas = meta["metadatas"]

# 3. Load model embedding
model = SentenceTransformer(EMBEDDING_MODEL)

# 4. Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# --------- Pipeline truy vấn ---------
def search_chunks(query,k):
    q_emb = model.encode([query])
    D, I = index.search(np.array(q_emb).astype(np.float32), k)
    results = []
    for idx in I[0]:
        if 0 <= idx < len(all_texts):
            results.append({
                "text": all_texts[idx],
                "meta": all_metas[idx]
            })
    return results

def answer_question(query, k=10, max_tokens=256):
    # 1. Kiểm tra cache chính xác
    answer = find_in_history(query)
    if answer:
        print("Trả về từ cache (exact)")
        return answer

    # Kiểm tra gần đúng (fuzzy)
    answer = find_in_history_fuzzy(query, threshold=87)  # bạn có thể thử tăng/giảm threshold
    if answer:
        print("Trả về từ cache (fuzzy)")
        return answer
    
    top_chunks = search_chunks(query, k=k)
    
    context = "\n".join([chunk["text"] for chunk in top_chunks])
    
    # 3. Ghép prompt tối ưu
    
    prompt = f"""Dựa trên tài liệu sau đây, hãy trả lời CHÍNH XÁC (chỉ loại bỏ những ý sai, giữ nguyên các ý của tài liệu), THÂN THIỆN cho câu hỏi bên dưới, chỉ bằng tiếng Việt.

Nếu không có thông tin nào được đưa lên, hãy trả lời: "Tôi chưa tìm thấy thông tin chính xác trong tài liệu."

Tài liệu:
{context}

CÂU HỎI: {query}
"""
    print("promt chatgpt",prompt)
    # 4. Gọi GPT (hoặc LLM bất kỳ)
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.1,
    )
    answer = response.choices[0].message.content.strip()
    save_history(query, answer)
    #print("Trả lời:", answer)
    return answer

