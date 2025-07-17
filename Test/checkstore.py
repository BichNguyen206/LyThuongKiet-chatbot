import json

file_path = "data/processed/thidua_chunks_rag.json"   # Đổi tên file đúng loại dữ liệu
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

bad_chunks = [i for i, chunk in enumerate(data) if "text" not in chunk or not isinstance(chunk["text"], str) or not chunk["text"].strip()]
if bad_chunks:
    print("Các dòng lỗi:", bad_chunks)
    # Xóa các dòng lỗi:
    data = [chunk for chunk in data if "text" in chunk and isinstance(chunk["text"], str) and chunk["text"].strip()]
    # Lưu lại file sạch
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Đã loại bỏ các chunk lỗi!")
else:
    print("Dữ liệu hoàn toàn OK!")
