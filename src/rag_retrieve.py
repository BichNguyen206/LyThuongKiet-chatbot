import os
import json
import faiss
import numpy as np
import openai
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from langdetect import detect
from deep_translator import GoogleTranslator
from question_normalizer import normalize_question
from cache import find_in_history, find_in_history_fuzzy, save_history
from collections import Counter
from transformers import AutoTokenizer, AutoModel
import torch
import time



# ------------------ CẤU HÌNH ------------------
EMBEDDING_MODEL = "bkai-foundation-models/vietnamese-bi-encoder"

VECTOR_STORE_PATH = "data/vector_store/vector_db.index"
META_PATH = "data/vector_store/vector_db_meta.json"

SOCIAL_VECTOR_STORE_PATH = "data/social_vector_store/social.index"
SOCIAL_META_PATH = "data/social_vector_store/social_meta.json"

PROMPT_TEMPLATE_PATH = "data/prompt.txt"
RULE_PATH = "data/rules/rules.json"

# ------------------ LOAD MODEL DUY NHẤT ------------------
tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
model = AutoModel.from_pretrained(EMBEDDING_MODEL)
model.eval()

# ------------------ EMBEDDING ------------------
def encode_with_bkai(texts, batch_size=16):
    embeddings = []
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            encoded = tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors="pt")
            attention_mask = encoded['attention_mask']
            output = model(**encoded)
            last_hidden = output.last_hidden_state
            mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
            sum_embeddings = torch.sum(last_hidden * mask_expanded, 1)
            sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
            batch_embeddings = (sum_embeddings / sum_mask).cpu().numpy()
            embeddings.extend(batch_embeddings)
    return np.array(embeddings)

# ------------------ LOAD VECTOR & META ------------------
def load_faiss_and_meta(vector_path, meta_path, text_key="texts", meta_key="metadatas"):
    index = faiss.read_index(vector_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    all_texts = meta[text_key]
    all_metas = meta[meta_key]
    return index, all_texts, all_metas

def load_social_faiss_and_meta():
    index = faiss.read_index(SOCIAL_VECTOR_STORE_PATH)
    with open(SOCIAL_META_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)
    questions = meta["questions"]
    answers = meta["answer"]
    return index, questions, answers
def load_rules():
    if not os.path.exists(RULE_PATH):
        return []
    with open(RULE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

main_index, main_texts, main_metas = load_faiss_and_meta(VECTOR_STORE_PATH, META_PATH)
social_index, social_questions, social_answers = load_social_faiss_and_meta()

# ------------------ NGÔN NGữ ------------------
def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

def translate_to_vietnamese(text):
    try:
        return GoogleTranslator(source='auto', target='vi').translate(text)
    except:
        return text

# ------------------ TÌM KIẾM Dắu LIỆU CHÍNH ------------------
def search_chunks(query, k=5):
    q_emb = encode_with_bkai([query])
    D, I = main_index.search(q_emb.astype(np.float32), k)
    results = []
    for idx in I[0]:
        if 0 <= idx < len(main_texts):
            results.append({
                "text": main_texts[idx],
                "meta": main_metas[idx]
            })
    return results

# ------------------ TÌM KIẾM Dắu LIỆU XÃ GIAO ------------------
def search_social_question(query, top_k=3):
    q_emb = encode_with_bkai([query])
    D, I = social_index.search(q_emb.astype(np.float32), top_k)
    results = []
    for rank, idx in enumerate(I[0]):
        if 0 <= idx < len(social_questions):
            results.append({
                "question": social_questions[idx],
                "answer": social_answers[idx],
                "score": D[0][rank]
            })
    return results

#------------------- Tìm kiếm theo rule-based--------------------

def check_rule_match(question):
    rules = load_rules()
    question_lower = question.lower()
    for rule in rules:
        for pattern in rule["patterns"]:
            if pattern.lower() in question_lower:
                return rule["response"]
    return None
#------------------- Lấy topic--------------------

def get_majority_source(chunks):
    sources = []
    for chunk in chunks:
        # Nếu chunk có metadata là dict chứa 'source'
        meta = chunk.get("metadata", {}) if "metadata" in chunk else chunk
        source = meta.get("source")
        if source:
            sources.append(source)
    if not sources:
        return ""
    topic, _ = Counter(sources).most_common(1)[0]
    return topic

# ------------------ TẠO PROMPT ------------------
def build_prompt(context, query):
    if os.path.exists(PROMPT_TEMPLATE_PATH):
        with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            template = f.read()
    else:
        template = "TÀI LIỆU:\n{context}\n\nCÂU HỌI: {query}\n\nTRẢ LỜI:"
    return template.replace("{context}", context).replace("{query}", query)

# ------------------ OPENAI API ------------------
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ------------------ Gọi GPT ------------------
def call_gpt_with_retry(prompt, max_tokens=256, retries=3, wait_time=40):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except openai.RateLimitError:
            print(f"[Retry {attempt+1}] Đã vượt giới hạn tốc độ, đợi {wait_time}s...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"[Error] {e}")
            break
    return "Xin lỗi, hiện tại hệ thống quá tải. Bạn vui lòng thử lại sau nhé!"

# ------------------ XỬ LÝ TRẢ LỜI ------------------
def answer_question(user_input, k=5, max_tokens=256):
    lang = detect_language(user_input)
    top_chunks=[]
    if lang != "vi":
        print(f"[!] Câu hỏi không phải tiếng Việt ({lang}) → đang dịch...")
        user_input = translate_to_vietnamese(user_input)
    rule_answer = check_rule_match(user_input)
    if rule_answer:
        return {
            "answer": rule_answer,
            "topic": "Rule-based"
        }

    social_res = search_social_question(user_input)
    if social_res and len(social_res) > 0:
        if social_res[0]["score"] < 1.0:
            return {"answer": social_res[0]["answer"], 
                    "topic": "Social"}

    query = normalize_question(user_input)
    
    answer = find_in_history(query)
    if answer:
        #print("Trả lời từ cache (exact)")
        return {"answer": answer, 
                "topic": "Ground Truth"}
    answer = find_in_history_fuzzy(query, threshold=87)
    if answer:
        #print("Trả lời từ cache (fuzzy)")
        return {"answer": answer, 
                "topic": "Ground Truth"}

    top_chunks = search_chunks(query, k=k)
    topic = get_majority_source(top_chunks)
    context = "\n".join([chunk["text"] for chunk in top_chunks])
    prompt = build_prompt(context, query)
    print("\U0001f9e0 Prompt gửi lên GPT:\n", prompt)

    answer = call_gpt_with_retry(prompt, max_tokens=max_tokens)
    save_history(query, answer)

    return {
        "answer": answer,
        "topic": topic
    }
