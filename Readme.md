# LyThuongKiet-chatbot

**LyThuongKiet-chatbot** là hệ thống Chatbot AI hỗ trợ học sinh trường THPT Lý Thường Kiệt tra cứu các thông tin quan trọng về trường, như: nội quy, thời khóa biểu, sơ đồ phòng học, thông tin giáo viên, lịch thi, điểm thi đua,...\
Dự án ứng dụng kỹ thuật RAG (Retrieval-Augmented Generation) để đảm bảo trả lời chính xác, cập nhật sát thực tế và dễ dàng mở rộng dữ liệu.

---

## 🌟 Tính năng nổi bật

- Tra cứu nội quy học sinh, sơ đồ phòng học, thời khóa biểu, lịch/phòng thi.
- Xem thông tin giáo viên, tổ chuyên môn.
- Dễ dàng cập nhật dữ liệu mới cho admin.
- Tối ưu tốc độ truy vấn nhờ cache các câu hỏi đã trả lời.
- Giao diện web trực quan, dễ sử dụng.

---

## 📁 Kiến trúc & cấu trúc thư mục

```
LyThuongKiet-chat-box/
│
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── environment.yml
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── vector_store/
│
├── docs/
│   ├── architecture.png
│   └── user_manual.md
│
├── src/
│   ├── config.py
│   ├── data_preprocessing.py
│   ├── embedding.py
│   ├── rag_backend.py
│   ├── admin_tools.py
│   └── cache.py
│
├── app/
│   ├── web/
│   │   ├── static/
│   │   ├── templates/
│   │   └── app.py
│   └── api/
│
├── tests/
│   ├── test_preprocessing.py
│   ├── test_embedding.py
│   └── test_rag_backend.py
│
├── scripts/
│   └── demo_chat.py
│
└── report/
    ├── final_report.md
    └── presentation.pptx
```

**Giải thích:**

- `data/`: Lưu dữ liệu gốc, dữ liệu đã xử lý và kho vector embedding.

- `docs/`: Tài liệu, hướng dẫn sử dụng, sơ đồ minh họa.

- `src/`: Mã nguồn xử lý (preprocess, embedding, backend RAG, công cụ admin...).

- `app/`: Giao diện người dùng (web, API).

- `report/`: Báo cáo, slide, tài liệu tổng kết dự án.

---

## ⚙️ Hướng dẫn cài đặt

### Yêu cầu

- Python >= 3.9
-

### 1. Cài đặt bằng pip

```bash
git clone https://github.com/<your-group>/LyThuongKiet-chatbot.git
cd LyThuongKiet-chat-box
pip install -r requirements.txt
```

### 2. (Tuỳ chọn) Cài đặt môi trường bằng Conda

```bash
conda env create -f environment.yml
conda activate lythuongkiet-chatbox
```

---

## 🚀 Hướng dẫn sử dụng nhanh

### 1. Tiền xử lý & nhúng dữ liệu

- Đưa toàn bộ dữ liệu vào thư mục `data/raw/`
- Chạy script tiền xử lý và tạo embedding:
  ```bash
  python src/data_preprocessing.py
  python src/embedding.py
  ```

### 2. Khởi động giao diện web

- Chạy ứng dụng web (ví dụ dùng Flask):
  ```bash
  python app/web/app.py
  ```
- Truy cập trình duyệt tại [http://localhost:5000](http://localhost:5000)

### 3. Demo chat qua terminal

```bash
python scripts/demo_chat.py
```

---

## 👩‍💼 Quy trình cập nhật dữ liệu (cho Admin)

1. Đăng nhập tài khoản admin trên giao diện web.
2. Upload file dữ liệu mới hoặc nhập thủ công.
3. Hệ thống tự động chuẩn hóa, sinh embedding và cập nhật vào kho vector.
4. Xoá/ghi đè embedding cũ nếu có dữ liệu thay thế.
5. Xoá cache các câu hỏi liên quan nếu cần.
6. Trả lởi thủ công các câu hỏi không có dữ liệu

---

## 📚 Tài liệu tham khảo

- [LangChain](https://python.langchain.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [OpenAI API](https://platform.openai.com/docs/)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)

---

## 📄 Giấy phép

Dự án phát hành theo giấy phép [MIT](LICENSE).

---

## 📞 Liên hệ

**Nhóm phát triển:**

- [Tên nhóm, thành viên, email] (Bổ sung sau)
- Trường THPT Lý Thường Kiệt

---

