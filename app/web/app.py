from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import subprocess
import os
import sys
from dotenv import load_dotenv
import openai
# Thêm đường dẫn src để import rag_retrieve.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from rag_retrieve import answer_question

# Đọc biến môi trường từ file .env
load_dotenv()
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

app = Flask(__name__)
app.secret_key = os.urandom(24)
DATA_TYPES = {
    "noiquy": {
        "label": "Nội quy",
        "file": "data/processed/noiquy_chunks_rag.json"
    },
    "gioithieutruong": {
        "label": "Giới thiệu trường",
        "file": "data/processed/gioithieu_chunks_rag.json"
    },
    "thidua": {
        "label": "Thi đua",
        "file": "data/processed/thidua_chunks_rag.json"
    }
    # Có thể bổ sung loại khác nếu muốn
}
DEFAULT_TYPE = "noiquy"
def log_unanswered_question(question):
    import json, os
    path = "data/unanswered_questions.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            unanswered = json.load(f)
    else:
        unanswered = []
    # Kiểm tra trùng (không ghi nhiều lần)
    for q in unanswered:
        if q["question"].strip().lower() == question.strip().lower():
            q["count"] += 1
            break
    else:
        from datetime import date
        unanswered.append({
            "question": question,
            "date": date.today().isoformat(),
            "count": 1
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(unanswered, f, ensure_ascii=False, indent=2)
@app.route("/ask", methods=["POST"])
def ask():
    question = request.form["question"]
    answer = answer_question(question)
    if answer == "Tôi chưa tìm thấy thông tin chính xác trong tài liệu.":
        log_unanswered_question(question)
    return jsonify({"answer": answer})
@app.route("/admin/unanswered", methods=["GET"])
def admin_unanswered():
    path = "data/unanswered_questions.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            unanswered = json.load(f)
    else:
        unanswered = []
    return render_template("admin_unanswered_list.html", unanswered=unanswered)
@app.route("/admin/answer_unanswered/<int:idx>", methods=["GET", "POST"])
def admin_answer_unanswered(idx):
    unanswered_path = "data/unanswered_questions.json"
    if os.path.exists(unanswered_path):
        with open(unanswered_path, "r", encoding="utf-8") as f:
            unanswered = json.load(f)
    else:
        unanswered = []
    question = unanswered[idx]["question"]
    if request.method == "POST":
        answer = request.form["answer"]
        topic = request.form["topic"]
        source = request.form["source"]
        # Thêm vào knowledge base
        new_chunk = {
            "text": answer,
            "metadata": {
                "section": topic,
                "source": source,
                "admin_answer_for": question,
                "updated_at": "2025-07-01"
            }
        }
        kb_path = "data/processed/noiquy_chunks_rag.json"
        if os.path.exists(kb_path):
            with open(kb_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)
        else:
            chunks = []
        chunks.append(new_chunk)
        with open(kb_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        # Thêm vào chat_history.json
        chat_history_path = "data/history/chat_history.json"
        os.makedirs(os.path.dirname(chat_history_path), exist_ok=True)
        try:
            with open(chat_history_path, "r", encoding="utf-8") as f:
                chat_history = json.load(f)
        except:
            chat_history = []
        chat_history.append({"question": question, "answer": answer})
        with open(chat_history_path, "w", encoding="utf-8") as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)
        # Xóa khỏi unanswered
        unanswered.pop(idx)
        with open(unanswered_path, "w", encoding="utf-8") as f:
            json.dump(unanswered, f, ensure_ascii=False, indent=2)
        return redirect(url_for('admin_unanswered'))
    return render_template("admin_unanswered.html", question=question)

@app.route("/", methods=["GET", "POST"])
def index():
    if session.get("logged_in"):
        return redirect(url_for("admin"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]
        if user == ADMIN_USERNAME and pw == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            error = "Sai tài khoản hoặc mật khẩu!"
    return render_template("login.html", error=error)
def load_chunks(dtype):
    path = DATA_TYPES[dtype]["file"]
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_chunks(dtype, chunks):
    path = DATA_TYPES[dtype]["file"]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

# --------- CRUD ---------
"""def load_chunks():
    with open("data/processed/noiquy_chunks_rag.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_chunks(chunks):
    with open("data/processed/noiquy_chunks_rag.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)"""

@app.route("/admin", methods=["GET"])
def admin():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    dtype = request.args.get("type", DEFAULT_TYPE)
    if dtype not in DATA_TYPES: dtype = DEFAULT_TYPE
    chunks = load_chunks(dtype)
    update_status = request.args.get("update_status")
    return render_template(
        "admin.html",
        chunks=chunks,
        update_status=update_status,
        dtype=dtype,
        data_types=DATA_TYPES
    )

@app.route("/admin/add", methods=["GET", "POST"])
def admin_add():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    dtype = request.args.get("type", DEFAULT_TYPE)
    if dtype not in DATA_TYPES: dtype = DEFAULT_TYPE

    if request.method == "POST":
        section = request.form.get("section", "")
        subsection = request.form.get("subsection", "")
        text = request.form.get("text", "")
        new_chunk = {
            "text": text,
            "metadata": {
                "section": section,
                "subsection": subsection,
                "updated_at": "2025-06-27"
            }
        }
        chunks = load_chunks(dtype)
        chunks.append(new_chunk)
        save_chunks(dtype, chunks)
        return redirect(url_for("admin", type=dtype))
    return render_template("admin_add.html", dtype=dtype, data_types=DATA_TYPES)

@app.route("/admin/edit/<int:idx>", methods=["GET", "POST"])
def admin_edit(idx):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    dtype = request.args.get("type", DEFAULT_TYPE)
    if dtype not in DATA_TYPES: dtype = DEFAULT_TYPE

    chunks = load_chunks(dtype)
    if idx < 0 or idx >= len(chunks):
        return "Không tìm thấy mục!", 404
    chunk = chunks[idx]
    if request.method == "POST":
        chunk["metadata"]["section"] = request.form.get("section", "")
        chunk["metadata"]["subsection"] = request.form.get("subsection", "")
        chunk["text"] = request.form.get("text", "")
        save_chunks(dtype, chunks)
        return redirect(url_for("admin", type=dtype))
    return render_template("admin_edit.html", idx=idx, chunk=chunk, dtype=dtype, data_types=DATA_TYPES)
@app.route("/admin/delete/<int:idx>", methods=["POST"])
def admin_delete(idx):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    dtype = request.args.get("type", DEFAULT_TYPE)
    if dtype not in DATA_TYPES: dtype = DEFAULT_TYPE

    chunks = load_chunks(dtype)
    if idx < 0 or idx >= len(chunks):
        return "Không tìm thấy mục!", 404
    chunks.pop(idx)
    save_chunks(dtype, chunks)
    return redirect(url_for("admin", type=dtype))
@app.route("/admin/update_vector_store", methods=["POST"])
def update_vector_store():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/embedding.py"))
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            update_status = "Thành công"
        else:
            update_status = "Lỗi khi cập nhật vector store:\n" + result.stderr
    except Exception as e:
        update_status = f"Lỗi khi cập nhật vector store: {str(e)}"
    return redirect(url_for("admin", update_status=update_status))

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
