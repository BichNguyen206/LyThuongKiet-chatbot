import os
import json
from fuzzywuzzy import fuzz

HISTORY_FILE = "data/history/chat_history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def save_history(question, answer):
    history = load_history()
    history.append({"question": question, "answer": answer})
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def find_in_history(question):
    """So khớp chính xác (chỉ cần giống 100%)"""
    q1 = question.strip().lower()
    for item in load_history():
        q2 = item["question"].strip().lower()
        if q1 == q2:
            return item["answer"]
    return None

def find_in_history_fuzzy(question, threshold=87):
    """So khớp gần đúng (giống >= threshold/100 điểm)"""
    q1 = question.strip().lower()
    best_score = 0
    best_answer = None
    for item in load_history():
        q2 = item["question"].strip().lower()
        score = fuzz.token_set_ratio(q1, q2)
        if score >= threshold and score > best_score:
            best_score = score
            best_answer = item["answer"]
    return best_answer
