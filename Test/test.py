import json
from fuzzywuzzy import fuzz
from time import sleep
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from rag_retrieve import answer_question

# Đọc bộ câu hỏi – đáp án
with open(os.path.join(os.path.dirname(__file__), "cau_hoi_thi_dua_lop.json"), "r", encoding="utf-8") as f:
    qa_pairs = json.load(f)

results = []
total = len(qa_pairs)
right_fuzzy = 0
wrong_cases = []

FUZZY_THRESHOLD = 85  # Ngưỡng fuzzy

for idx, qa in enumerate(qa_pairs, 1):
    q = qa['question']
    expected = qa['answer']

    try:
        response = answer_question(q)
    except Exception as e:
        response = f"LỖI: {e}"

    # Đánh giá fuzzy
    score = fuzz.token_set_ratio(expected, response)
    is_fuzzy = score >= FUZZY_THRESHOLD

    if is_fuzzy:
        right_fuzzy += 1
    else:
        # Chỉ in các trường hợp sai
        print(f"\n--- CÂU TRẢ LỜI SAI ({idx}) ---")
        print(f"Câu hỏi    : {q}")
        print(f"Đáp án mẫu : {expected}")
        print(f"Chatbot    : {response}")
        print(f"Fuzzy score: {score}")

        # Lưu vào danh sách sai để xuất file riêng (nếu muốn)
        wrong_cases.append({
            "index": idx,
            "question": q,
            "expected": expected,
            "response": response,
            "fuzzy_score": score
        })

    results.append({
        "question": q,
        "expected": expected,
        "response": response,
        "is_fuzzy": is_fuzzy,
        "fuzzy_score": score
    })
    sleep(1.5)  # Tránh tắc API

# Kết quả tổng hợp
print("\n--- KẾT QUẢ TỔNG HỢP ---")
print(f"ĐÚNG FUZZY: {right_fuzzy}/{total} ({right_fuzzy/total*100:.1f}%)")

# Độ chính xác fuzzy
accuracy_fuzzy = right_fuzzy / total
print(f"\nĐộ chính xác FUZZY: {accuracy_fuzzy:.2%}")

# Lưu tất cả kết quả và các trường hợp sai ra file
with open("ket_qua_danh_gia.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

with open("cau_tra_loi_sai.json", "w", encoding="utf-8") as f:
    json.dump(wrong_cases, f, ensure_ascii=False, indent=2)

print("\nĐã lưu chi tiết kết quả vào file 'ket_qua_danh_gia.json'")
print("Đã lưu các câu trả lời sai vào file 'cau_tra_loi_sai.json'")
