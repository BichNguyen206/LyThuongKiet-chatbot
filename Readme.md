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
LYTHUONGKIET-CHATBOT/
├── app/                            # Giao diện người dùng và điều phối truy vấn
│   ├── app.py                      # Điểm khởi động Flask app
│   └── web/                        # Giao diện người dùng
│       ├── static/
│       │   ├── style.css           # Tệp định dạng giao diện
│       │   └── ts.png              # Hình ảnh sử dụng trong giao diện
│       └── templates/              # Các tệp HTML cho admin và giao diện chính
│           ├── index.html
│           ├── login.html
│           ├── admin.html
│           ├── admin_add.html
│           ├── admin_edit.html
│           ├── admin_unanswered.html
│           └── admin_unanswered_list.html
├── data/                           # Dữ liệu lưu trữ và truy vấn
│   ├── history/
│   │   └── chat_history.json       # Bộ nhớ đệm truy vấn
│   ├── processed/                  # Các chunk văn bản đã xử lý
│   │   ├── gioithieu_chunks_rag.json
│   │   ├── noiquy_chunks_rag.json
│   │   └── thidua_chunks_rag.json
│   ├── vector_store/              # FAISS index và metadata
│   │   ├── vector_db.index
│   │   └── vector_db_meta.json
│   └── unanswered_questions.json   # Các câu hỏi chưa có phản hồi
├── src/                            # Các module xử lý chính
│   ├── __init__.py
│   ├── cache.py                    # So khớp câu hỏi trong cache
│   ├── data_preprocessing.py       # Tiền xử lý và phân đoạn văn bản
│   ├── embedding.py                # Nhúng văn bản và tạo FAISS index
│   └── rag_retrieve.py             # Pipeline truy vấn: FAISS → GPT
├── Test/                           # Thư mục kiểm thử
│   ├── test.py                     # Thực thi kiểm thử tự động
│   ├── test_query.py               # Kiểm thử truy vấn cụ thể
│   ├── Test_tong_hop.json          # Tập dữ liệu 100 câu hỏi
│   ├── ket_qua_danh_gia.json       # Kết quả đánh giá hệ thống
│   └── cau_tra_loi_sai.json        # Các câu trả lời sai (để phân tích)
├── requirements.txt                # Khai báo các thư viện phụ thuộc
└── README.md                       # Tài liệu hướng dẫn cài đặt và sử dụng

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

