# LyThuongKiet-chatbot

**LyThuongKiet-chatbot** là hệ thống Chatbot AI hỗ trợ học sinh trường THPT Lý Thường Kiệt tra cứu các thông tin quan trọng về trường, như: nội quy, thông tin giáo viên, điểm thi đua,...\
Dự án ứng dụng kỹ thuật RAG (Retrieval-Augmented Generation) để đảm bảo trả lời chính xác, cập nhật sát thực tế và dễ dàng mở rộng dữ liệu.

---

## 🌟 Tính năng nổi bật

- Tra cứu nội quy học sinh, thông tin trường, điểm thi đua...
- Xem thông tin giáo viên, tổ chuyên môn.
- Dễ dàng cập nhật dữ liệu mới cho admin.
- Tối ưu tốc độ truy vấn nhờ cache các câu hỏi đã trả lời.
- Giao diện web trực quan, dễ sử dụng.

---

## 📁 Kiến trúc & cấu trúc thư mục

```
LyThuongKiet-chatbot/
├── .env                        # File cấu hình biến môi trường (API key, mode, ...)
├── .gitignore                  # Danh sách file/thư mục không push lên Git
├── git_push.bat                # Script đẩy code lên Git nhanh (Windows)
├── Readme.md                   # Tài liệu hướng dẫn dự án
├── requirements.txt            # Danh sách thư viện Python cần cài
│
├── app/
│   └── web/
│       ├── app.py                  # File chính chạy Flask Web App (backend + route)
│       ├── static/                 # Tài nguyên tĩnh cho giao diện (CSS, hình ảnh, ...)
│       │   ├── style.css           # CSS giao diện web
│       │   └── ts.png              # Ảnh minh họa (logo/trường, ...)
│       └── templates/              # Template HTML (Jinja2) cho Flask
│           ├── admin_dashboard.html      # Giao diện dashboard admin
│           ├── admin_edit.html           # Giao diện chỉnh sửa thông tin
│           ├── admin_unanswered_list.html# Giao diện danh sách câu hỏi chưa trả lời
│           ├── chat.html                 # Template chat cho user đã đăng nhập 
│           ├── index.html                # Trang chủ chatbot (sử dụng khi chưa đăng nhập)
│           ├── login.html                # Đăng nhập
│           └── register.html             # Đăng ký tài khoản
│
├── data/
│   ├── hard_replacements.json      # Quy tắc thay thế cố định (chuẩn hóa câu hỏi)
│   ├── prompt.txt                  # Prompt cho AI/gợi ý hệ thống
│   ├── unanswered_questions.json   # Lưu lại câu hỏi chưa có đáp án (tạm thời)
│   ├── users.json                  # Dữ liệu người dùng
│   │
│   ├── feedback/                   # Đánh giá câu trả lời của user
│   │   └── feedback_hs001.json
│   ├── history/                    
│   │   ├── chat_history.json       # ủa user
│   │   └── history_hs001.json
│   ├── logs/                       # Log hoạt động hệ thống (chuẩn hóa, lỗi, ...)
│   │   └── question_normalization_log.jsonl
│   ├── notifications/              # Thông báo gửi cho user
│   │   └── notify_hs001.json
│   ├── processed/                  # Dữ liệu đã xử lý cho mô hình RAG
│   │   ├── gioithieu_chunks_rag.json
│   │   ├── noiquy_chunks_rag.json
│   │   ├── social_responses.json
│   │   └── thidua_chunks_rag.json
│   ├── social_vector_store/        # Vector store cho các câu chào
│   │   ├── social.index
│   │   └── social_meta.json
│   └── vector_store/               # Vector store chính cho truy vấn RAG
│       ├── vector_db.index
│       └── vector_db_meta.json
│
├── src/
│   ├── cache.py                    # Module quản lý cache Q&A
│   ├── data_preprocessing.py       # Tiền xử lý dữ liệu
│   ├── embedding.py                # Sinh embedding (vector hóa dữ liệu)
│   ├── question_normalizer.py      # Module chuẩn hóa câu hỏi đầu vào
│   ├── rag_retrieve.py             # Logic chính: truy vấn RAG
│   ├── user_utils.py               # Xử lý thao tác liên quan đến user
│   ├── __init__.py                 
│  
│
└── Test/
    ├── checkstore.py               # Kiểm thử vector store hoặc cache
    ├── test.py                     # Test chức năng tổng hợp
    ├── test_query.py               # Test truy vấn RAG hoặc search
    ├── Test_tong_hop.json          # Bộ dữ liệu test tổng hợp
    └── test_user.py                # Test chức năng user/login


```

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

