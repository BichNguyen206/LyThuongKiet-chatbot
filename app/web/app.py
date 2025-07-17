import sys
import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
#import datetime
from datetime import datetime
#from datetime import date
import subprocess
from collections import defaultdict, Counter
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from rag_retrieve import answer_question, load_rules
from user_utils import check_login, load_users,hash_password, save_users
CACHE_PATH = "data/history/chat_history.json"
app = Flask(__name__)
app.secret_key = "supersecret"

def safe_load_json(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []
@app.template_filter('viet_month')
def viet_month(month_str):
    year, month = month_str.split('-')
    return f"Tháng {int(month)}/{year}"
# ---- Helper decorator phân quyền ----
def login_required(role=None):
    def decorator(f):
        def wrapper(*args, **kwargs):
            if not session.get("logged_in"):
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Bạn không có quyền truy cập.")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

def month_str(ts):
    try:
        return ts[:7]
    except:
        return ""

def load_chat_history():
    if not os.path.exists(CACHE_PATH):
        return []
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_chat_history(history):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
#======== Thống kê ====
#thống kê theo month và topic
def advanced_stats_by_month_and_topic():
    TOPICS = ["Nội quy", "Thông tin trường", "thi đua","Rep by admin", "Ground Truth","Social"]
    TOPICS_LOWER = [t.lower() for t in TOPICS]
    data_dir = os.path.join("data", "history")
    all_logs = []
    for file in os.listdir(data_dir):
        if file.startswith("history_") and file.endswith(".json"):
            username = file[len("history_"):-len(".json")]
            with open(os.path.join(data_dir, file), encoding="utf-8") as f:
                logs = json.load(f)
                for item in logs:
                    item["username"] = username
                    all_logs.append(item)

    # Thống kê user theo tháng
    user_month_counter = defaultdict(Counter)
    for entry in all_logs:
        user = entry["username"]
        mstr = month_str(entry.get("timestamp", ""))
        if mstr:
            user_month_counter[user][mstr] += 1

    # Thống kê theo chủ đề (không phân biệt hoa/thường)
    topic_month_counter = {topic: Counter() for topic in TOPICS}
    for entry in all_logs:
        mstr = month_str(entry.get("timestamp", ""))
        topic_raw = entry.get("topic", "")
        topic = topic_raw.strip().lower()
        for idx, t in enumerate(TOPICS_LOWER):
            if topic == t:
                topic_month_counter[TOPICS[idx]][mstr] += 1

    # Danh sách chưa trả lời
    unanswered_questions = [
        {
            "username": entry["username"],
            "question": entry.get("question", ""),
            "timestamp": entry.get("timestamp", ""),
            "topic": entry.get("topic", "")
        }
        for entry in all_logs
        if not entry.get("answered")
    ]

    return {
        "user_month_stats": user_month_counter,
        "topic_month_stats": topic_month_counter,
        "unanswered_questions": unanswered_questions
    }


# ---- Trang chủ, điều hướng phân quyền ----
@app.route("/")
def index():
    if not session.get("logged_in"):
        return render_template("index.html")
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("chat"))

# ---- Đăng nhập/Đăng xuất/regis----
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = check_login(username, password)
        if user:
            session["logged_in"] = True
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["user_id"] = user["user_id"]
            flash("Đăng nhập thành công.")
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("chat"))
        error = "Sai tài khoản hoặc mật khẩu!"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("chatbox", None)
    session.clear()
    return redirect(url_for("index"))
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = False
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        class_name = request.form['class']
        if password != confirm_password:
            error = "Mật khẩu không khớp!"
        else:
            users = load_users()
            if any(u['username'] == username for u in users):
                error = "Tên đăng nhập đã tồn tại!"
            else:
                new_user = {
                    "user_id": str(len(users)+1),
                    "username": username,
                    "password_hash": hash_password(password),
                    "role": "student",
                    "fullname": fullname,
                    "class": class_name,
                    "email": email
                }
                users.append(new_user)
                save_users(users)
                success = True
                # Đừng return redirect ngay, mà return template có thông báo
                return render_template('register.html', success=success)
    return render_template('register.html', error=error)

#------xử lý câu chưa có thông tin -----
@app.route('/admin/answer_unanswered', methods=['POST'])
def admin_answer_unanswered():
    username = request.form.get('username')
    timestamp = request.form.get('timestamp')
    question = request.form.get('question')
    admin_answer = request.form.get('admin_answer', '').strip()

    if not (username and timestamp and question and admin_answer):
        flash("Thiếu thông tin hoặc chưa nhập đáp án.", "warning")
        return redirect(url_for('admin_dashboard', tab='stats'))

    # Load file history của user
    history_file = f"data/history/history_{username}.json"
    
    if not os.path.exists(history_file):
        flash("Không tìm thấy lịch sử người dùng.", "danger")
        return redirect(url_for('admin_dashboard', tab='stats'))

    import json
    with open(history_file, encoding="utf-8") as f:
        history = json.load(f)
    updated = False
    for entry in history:
        if entry.get("timestamp") == timestamp and entry.get("question") == question:
            entry["answer"] = admin_answer
            entry["answered"] = True
            entry["status"] = "answered"
            entry["topic"] = "Rep by admin"
            updated = True
            break
    if updated:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        update_cache_with_admin_answer(question, admin_answer)
        add_or_update_notification_for_user(username, question, admin_answer, entry.get("topic", ""))
        flash("Đã cập nhật đáp án.", "success")
    else:
        flash("Không tìm thấy câu hỏi để cập nhật.", "danger")
    
    return redirect(url_for('admin_dashboard', tab='stats'))
def add_or_update_notification_for_user(username, question, answer, topic):
    notif_dir = "data/notifications"
    os.makedirs(notif_dir, exist_ok=True)
    notif_file = os.path.join(notif_dir, f"notify_{username}.json")
    notifs = []
    if os.path.exists(notif_file):
        with open(notif_file, encoding="utf-8") as f:
            notifs = json.load(f)
    updated = False
    for n in notifs:
        if n["question"] == question:
            n["answer"] = answer
            n["topic"] = topic
            n["status"] = "new"
            updated = True
            break
    if not updated:
        # Nếu chưa từng gửi, thêm mới
        notifs.append({
            "question": question,
            "answer": answer,
            "topic": topic,
            "status": "new"
        })
    with open(notif_file, "w", encoding="utf-8") as f:
        json.dump(notifs, f, ensure_ascii=False, indent=2)

def load_unanswered_questions():
    data_dir = os.path.join("data", "history")
    result = []
    for file in os.listdir(data_dir):
        if file.startswith("history_") and file.endswith(".json"):
            username = file[len("history_"):-len(".json")]
            with open(os.path.join(data_dir, file), encoding="utf-8") as f:
                logs = json.load(f)
                for entry in logs:
                    if not entry.get("answered"):
                        result.append({
                            "username": username,
                            "question": entry.get("question", ""),
                            "timestamp": entry.get("timestamp", ""),
                            "topic": entry.get("topic", "")
                        })
    return result
def normalize_question(text):
    if not text:
        return ""
    # Viết thường, bỏ khoảng trắng 2 đầu, loại bỏ ký tự đặc biệt cuối câu, nhiều khoảng trắng -> 1
    text = text.strip().lower()
    text = re.sub(r'[^\w\s]', '', text)       # Loại dấu câu
    text = re.sub(r'\s+', ' ', text)          # Nhiều khoảng trắng thành 1
    return text

def update_cache_with_admin_answer(question, new_answer):
    cache_file =f"data/history/chat_history.json"
    cache = {}
    # Đọc cache hiện tại (nếu có)
    norm_question = normalize_question(question)
    if os.path.exists(cache_file):
        with open(cache_file, encoding="utf-8") as f:
            cache = json.load(f)
    # Xóa tất cả entry cũ có câu hỏi "tương đương"
    cache = [item for item in cache if normalize_question(item.get("question", "")) != norm_question]
    # Thêm entry mới
    cache.append({
        "question": question.strip(),
        "answer": new_answer
    })
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
# ---- Giao diện CHAT cho user/student ----
@app.route("/chat")
@login_required()
def chat():
    
    username = session.get("username")
    history_file = f"data/history/history_{username}.json"
    notif_file = f"data/notifications/notify_{username}.json"

    # Lấy lịch sử chat
    history = []
    if os.path.exists(history_file):
        history = safe_load_json(history_file)

    # Lấy notification (thông báo admin đã trả lời)
    notifications = []
    if os.path.exists(notif_file):
        notifications = safe_load_json(notif_file)
    notify_new = [n for n in notifications if n.get("status") == "new"]
    notify_count = len(notify_new)

    # Lịch sử chat của phiên này (session)
    if "chatbox" not in session:
        session["chatbox"] = []
    chatbox = session["chatbox"]

    return render_template(
        "chat.html",
        chatbox=chatbox,
        history=history,
        notify_count=notify_count,  # Số badge chuông
        notifications=notify_new    # Danh sách thông báo mới
    )
    

# ---- Route xử lý AJAX chat realtime (API) ----

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question")
    if not question:
        return {"error": "No question provided"}, 400

    result = answer_question(question)
    answer = result["answer"]
    topic = result["topic"]

    # Nếu đã đăng nhập, mới lưu history
    if session.get("logged_in"):
        username = session.get("username")
        history_file = f"data/history/history_{username}.json"

        # Lấy history từ file
        history = []
        if os.path.exists(history_file):
            history = safe_load_json(history_file)

        # Lịch sử chat trong phiên (session)
        if "chatbox" not in session:
            session["chatbox"] = []
        chatbox = session["chatbox"]

        chatbox.append({"question": question, "answer": answer})
        session["chatbox"] = chatbox  # Cập nhật session

        # Xác định trạng thái trả lời
        answer_text = answer.strip().lower()
        if ("chưa tìm thấy" in answer_text) or ("không có thông tin" in answer_text) or (not answer.strip()):
            answered = False
            status = "waiting"
        else:
            answered = True
            status = "answered"

        # Lưu vào history (gồm cả trạng thái notification)
        history.append({
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
            "answered": answered,
            "status": status,
            "topic" : topic,
        })
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)



    # Nếu chưa đăng nhập, chỉ trả lời, không lưu gì cả
    return {"answer": answer}
@app.route('/rate_answer', methods=['POST'])
@app.route('/rate_answer', methods=['POST'])
def rate_answer():
    if not session.get("logged_in"):
        return redirect(url_for('login'))
    username = session.get("username")
    question = request.form.get("question")
    answer = request.form.get("answer")
    rate = request.form.get("rate")  # 'like' hoặc 'unlike'

    # 1. Cập nhật file feedback cá nhân, chỉ 1 lần mỗi cặp Q&A
    rate_dir = "data/feedback"
    os.makedirs(rate_dir, exist_ok=True)
    rate_file = os.path.join(rate_dir, f"feedback_{username}.json")
    feedback = []
    found = False
    if os.path.exists(rate_file):
        with open(rate_file, encoding="utf-8") as f:
            feedback = json.load(f)
        for fb in feedback:
            if fb["question"] == question and fb["answer"] == answer:
                fb["rate"] = rate  # Update loại đánh giá mới nhất
                fb["timestamp"] = datetime.now().isoformat()
                found = True
                break
    if not found:
        feedback.append({
            "question": question,
            "answer": answer,
            "rate": rate,
            "timestamp": datetime.now().isoformat()
        })
    with open(rate_file, "w", encoding="utf-8") as f:
        json.dump(feedback, f, ensure_ascii=False, indent=2)

    # 2. Đếm lại tổng số like/unlike cho cặp Q&A này từ tất cả file feedback, rồi cập nhật vào history user
    total_like = 0
    total_unlike = 0
    feedback_dir = "data/feedback"
    for fname in os.listdir(feedback_dir):
        if fname.startswith("feedback_") and fname.endswith(".json"):
            with open(os.path.join(feedback_dir, fname), encoding="utf-8") as f:
                user_feedback = json.load(f)
                for fb in user_feedback:
                    if fb["question"] == question and fb["answer"] == answer:
                        if fb["rate"] == "like":
                            total_like += 1
                        elif fb["rate"] == "unlike":
                            total_unlike += 1

    # 3. Cập nhật trường like/unlike vào history của tất cả user từng hỏi câu này (nếu muốn chỉ update cho user hiện tại thì chỉ cần file history_{username}.json)
    history_file = f"data/history/history_{username}.json"
    if os.path.exists(history_file):
        with open(history_file, encoding="utf-8") as f:
            history = json.load(f)
        for entry in history:
            if entry.get("question") == question and entry.get("answer") == answer:
                entry["like"] = total_like
                entry["unlike"] = total_unlike
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    flash("Cảm ơn bạn đã đánh giá!", "success")
    return redirect(request.referrer or url_for('chat'))
import os, json
from collections import defaultdict

def get_like_unlike_stats():
    feedback_dir = "data/feedback"
    # key: (question, answer) → value: {'like': set(users), 'unlike': set(users)}
    stats = defaultdict(lambda: {"like": set(), "unlike": set()})
    for fname in os.listdir(feedback_dir):
        if fname.startswith("feedback_") and fname.endswith(".json"):
            username = fname[len("feedback_"):-len(".json")]
            with open(os.path.join(feedback_dir, fname), encoding="utf-8") as f:
                feedbacks = json.load(f)
                for fb in feedbacks:
                    key = (fb.get("question", ""), fb.get("answer", ""))
                    rate = fb.get("rate")
                    if rate == "like":
                        stats[key]["like"].add(username)
                    elif rate == "unlike":
                        stats[key]["unlike"].add(username)
    return stats
@app.route('/admin_supplement_answer', methods=['POST'])
def admin_supplement_answer():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for('login'))
    question = request.form.get('question')
    old_answer = request.form.get('old_answer')
    new_answer = request.form.get('new_answer')
    # TODO: Ghi lại lịch sử/sửa vào nơi lưu đáp án, có thể append vào cache hoặc history, và log lại cho thống kê
    # Ví dụ: thêm vào cache (nâng cấp nếu cần)
    update_cache_with_admin_answer(question, new_answer)
    flash("Đã cập nhật đáp án bổ sung!", "success")
    return redirect(url_for('admin_dashboard', tab='stats'))


# ---- Chuông thông báo - User xem đã đọc ----
@app.route("/clear_notify")
@login_required()
def clear_notify():
    username = session.get("username")
    notify_file = f"data/notify_{username}.json"
    notifications = []
    if os.path.exists(notify_file):
        notifications = safe_load_json(notify_file)
    for n in notifications:
        if n.get("status") == "new":
            n["status"] = "read"
    with open(notify_file, "w", encoding="utf-8") as f:
        json.dump(notifications, f, ensure_ascii=False, indent=2)
    return redirect(url_for("chat"))

# ---- ADMIN: Dashboard ----
def extract_section_tree(chunks):
    tree = {}  # section -> subsection -> items
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        section = meta.get("section", "")
        subsection = meta.get("subsection", "")
        item = meta.get("item", "")
        if not section: continue
        if section not in tree: tree[section] = {}
        if subsection:
            if subsection not in tree[section]: tree[section][subsection] = set()
            if item: tree[section][subsection].add(item)
    # Convert set to list for Jinja2/JS
    for sec in tree:
        for sub in tree[sec]:
            tree[sec][sub] = list(tree[sec][sub])
    return tree
@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    # Kiểm tra quyền admin
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    tab = request.args.get("tab", "data")
    update_status = request.args.get("update_status")
    context = {
        "tab": tab,
        "update_status": update_status,
        "data_types": DATA_TYPES,
        "section_tree": {}  # Mặc định là dict rỗng
    }
       
    if tab == "cache":
        cache = load_chat_history() 
        context["cache"] = cache
        context["unanswered_questions"] = []  # THÊM DÒNG NÀY

    elif tab == "users":
        users = load_users()
        unanswered_questions = load_unanswered_questions()
        context["users"] = users
        context["unanswered_questions"] = unanswered_questions
    elif tab == "stats":
        # Thống kê người dùng, câu hỏi chưa trả lời, v.v.
        users = load_users()
        unanswered_questions = load_unanswered_questions()
        context["user_count"] = len(users)
        context["unanswered_count"] = len(unanswered_questions)
        context["unanswered_questions"] = unanswered_questions
        like_unlike_stats = get_like_unlike_stats()
        context["like_unlike_stats"] = like_unlike_stats

        # ====== BỔ SUNG: Thống kê nâng cao ======
        stats = advanced_stats_by_month_and_topic() 
        context["user_month_stats"] = stats["user_month_stats"]
        context["topic_month_stats"] = stats["topic_month_stats"]
        # context["other_stats"] = stats["other_stats"]  # nếu có thêm
    elif tab == "rules":
        rules = load_rules()
        context["rules"] = rules
    else:
        dtype = request.args.get("type", DEFAULT_TYPE)
        if dtype not in DATA_TYPES:
            dtype = DEFAULT_TYPE
        chunks = load_chunks(dtype)
        sources = [chunk.get("metadata", {}).get("source") for chunk in chunks if "metadata" in chunk and "source" in chunk["metadata"]]
        sources = list({s for s in sources if s})
        default_source = sources[0] if sources else DATA_TYPES[dtype]["label"]
        section_tree = extract_section_tree(chunks)
        context.update({
            "dtype": dtype,
            "chunks": chunks,
            "section_tree": section_tree,
            "default_source": default_source,
            "unanswered_questions": []   # THÊM DÒNG NÀY
        })

    reset_user = request.args.get("reset_user")
    reset_pwd = request.args.get("reset_pwd")
    context.update({"reset_user": reset_user, "reset_pwd": reset_pwd})
    return render_template("admin_dashboard.html", **context)

# ---- ADMIN: Quản lý chunk kiến thức ----
# Lưu chunk mới hoặc cập nhật chunk hiện tại

@app.route("/admin/save_chunk", methods=["POST"])
def admin_save_chunk():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login"))
    dtype = request.args.get("type", DEFAULT_TYPE)
    if dtype not in DATA_TYPES: dtype = DEFAULT_TYPE

    idx = request.form.get("idx", "")
    text = request.form.get("text", "").strip()
    section = request.form.get("section", "")
    subsection = request.form.get("subsection", "")
    item = None  # Mặc định null
    source = DATA_TYPES[dtype]["label"]
    chunkid = request.form.get("chunkid", "")

    if not text:
        return redirect(url_for("admin_dashboard", type=dtype, update_status="Nội dung không được để trống!"))

    # Lấy ID nếu không có thì sinh tự động
    if not chunkid:
        import uuid
        chunkid = "chunk_" + str(uuid.uuid4())[:8]

    chunks = load_chunks(dtype)
    chunk_data = {
        "text": text,
        "metadata": {
            "section": section,
            "subsection": subsection,
            "item": item if item else None,
            "source": source,
            "updated_at": datetime.now().strftime("%Y-%m-%d"),
            "id": chunkid
        }
    }
    if idx == "":  # Thêm mới
        chunks.append(chunk_data)
    else:          # Sửa dòng có index = idx
        idx = int(idx)
        if idx < 0 or idx >= len(chunks):
            return redirect(url_for("admin_dashboard", type=dtype, update_status="Không tìm thấy mục!"))
        chunks[idx] = chunk_data

    save_chunks(dtype, chunks)
    return redirect(url_for("admin_dashboard", type=dtype, update_status="success"))

# Xóa 1 chunk
@app.route("/admin/delete_chunk", methods=["POST"])
def admin_delete_chunk():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login"))
    dtype = request.args.get("type", DEFAULT_TYPE)
    if dtype not in DATA_TYPES: dtype = DEFAULT_TYPE

    idx = int(request.form.get("chunk_id"))
    chunks = load_chunks(dtype)
    if idx < 0 or idx >= len(chunks):
        return "Không tìm thấy mục!", 404
    chunks.pop(idx)
    save_chunks(dtype, chunks)
    return redirect(url_for("admin_dashboard", type=dtype))
#--update vector    
@app.route("/admin/update_vector_store", methods=["POST"])
def update_vector_store():
    if not session.get("logged_in") or session.get("role") != "admin":
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
            update_status = "success"
        else:
            update_status = "Lỗi khi cập nhật vector store:\n" + result.stderr
    except Exception as e:
        update_status = f"Lỗi khi cập nhật vector store: {str(e)}"
    return redirect(url_for("admin_dashboard", update_status=update_status))
@app.route("/admin/cache/edit/<int:idx>", methods=["POST"])
def admin_cache_edit(idx):
    cache = load_chat_history()
    question = request.form.get("question")
    answer = request.form.get("answer")
    if 0 <= idx < len(cache):
        cache[idx]["question"] = question
        cache[idx]["answer"] = answer
        save_chat_history(cache)
        flash("Đã cập nhật cache thành công!")
    else:
        flash("Cập nhật thất bại, index không hợp lệ!", "error")
    return redirect(url_for("admin_dashboard", tab="cache"))


#========Quản lý user=========
@app.route('/admin/users/delete/<user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    users = load_users()
    users = [u for u in users if u['user_id'] != user_id]
    save_users(users)
    return redirect(url_for('admin_dashboard', tab='users'))


@app.route("/admin/reset_password/<user_id>", methods=["POST"])
def admin_reset_password(user_id):
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for('login'))

    users = load_users()
    new_password = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    hashed_password = hash_password(new_password)

    reset_username = None
    for user in users:
        if user["user_id"] == user_id:
            user["password_hash"] = hashed_password
            reset_username = user["username"]
            break

    save_users(users)

    # Lưu tạm thông tin reset vào session (hoặc truyền qua URL nếu muốn)
    session['reset_user'] = reset_username
    session['reset_pwd'] = new_password

    return redirect(url_for('admin_dashboard', tab="users"))
@app.route("/admin/clear_reset_popup", methods=["POST"])
def clear_reset_popup():
    session.pop('reset_pwd', None)
    session.pop('reset_user', None)
    return '', 204

    # Lưu mật khẩu mới ra context hoặc dùng Flask flash
    # Ở đây dùng redirect truyền tạm qua query string (hoặc bạn có thể dùng Flask flash)
    return redirect(url_for('admin_dashboard', tab="users", reset_user=reset_username, reset_pwd=new_password))
@app.route('/admin/edit_user', methods=['POST'])
def admin_edit_user():
    if not session.get("logged_in") or session.get("role") != "admin":
        return jsonify(success=False)
    data = request.get_json()
    user_id = data.get("user_id")
    fullname = data.get("fullname")
    email = data.get("email")
    class_name = data.get("class")
    role = data.get("role") 
    users = load_users()
    for u in users:
        if u["user_id"] == user_id:
            u["fullname"] = fullname
            u["email"] = email
            u["class"] = class_name
            if role:
                u["role"] = role  
    save_users(users)
    return jsonify(success=True)

# ---- ADMIN: Quản lý câu hỏi ----
@app.route("/admin/unanswered")
@login_required(role="admin")
def admin_unanswered():
    import glob
    unanswered = []
    for file in glob.glob("data/notify_*.json"):
        username = file.split("_")[-1].replace(".json", "")
        with open(file, "r", encoding="utf-8") as f:
            notify = json.load(f)
            for n in notify:
                if n.get("status") == "waiting":
                    unanswered.append({"username": username, "question": n["question"]})
    return render_template("admin_unanswered_list.html", unanswered=unanswered)

@app.route("/admin/notify_update", methods=["POST"])
@login_required(role="admin")
def admin_notify_update():
    username = request.form.get("username")
    question = request.form.get("question")
    answer = request.form.get("answer")
    notify_file = f"data/notify_{username}.json"
    notifications = []
    if os.path.exists(notify_file):
        with open(notify_file, "r", encoding="utf-8") as f:
            notifications = json.load(f)
    for n in notifications:
        if n["question"] == question and n.get("status") == "waiting":
            n["answer"] = answer
            n["status"] = "new"
    with open(notify_file, "w", encoding="utf-8") as f:
        json.dump(notifications, f, ensure_ascii=False, indent=2)
    return redirect(url_for("admin_unanswered"))
# Admin trả lời câu hỏi
@app.route('/admin/answer_question', methods=['POST'])
def admin_answer_question():
    if not session.get("logged_in") or session.get("role") != "admin":
        return jsonify(success=False)
    data = request.get_json()
    user_id = data.get("user_id")
    question = data.get("question")
    answer = data.get("answer")
    try:
        with open('data/unanswered_questions.json', 'r', encoding='utf-8') as f:
            qlist = json.load(f)
        for item in qlist:
            if item.get("user_id") == user_id and item.get("question") == question and item.get("status") == "waiting":
                item["status"] = "answered"
                item["answer"] = answer
        with open('data/unanswered_questions.json', 'w', encoding='utf-8') as f:
            json.dump(qlist, f, ensure_ascii=False, indent=2)
        return jsonify(success=True)
    except Exception as e:
        print("Error:", e)
        return jsonify(success=False)

# ==== CRUD Knowledge Base (KB) cho admin ====
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
}
DEFAULT_TYPE = "noiquy"

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

@app.route("/admin/database")
@login_required(role="admin")
def admin_database():
    dtype = request.args.get("type", DEFAULT_TYPE)
    if dtype not in DATA_TYPES: dtype = DEFAULT_TYPE
    chunks = load_chunks(dtype)
    update_status = request.args.get("update_status")
    return render_template(
        "admin_database.html",
        chunks=chunks,
        update_status=update_status,
        dtype=dtype,
        data_types=DATA_TYPES
    )

@app.route("/admin/add", methods=["GET", "POST"])
@login_required(role="admin")
def admin_add():
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
        flash("Đã thêm mới mục kiến thức.")
        return redirect(url_for("admin_database", type=dtype))
    return render_template("admin_add.html", dtype=dtype, data_types=DATA_TYPES)

@app.route("/admin/edit/<int:idx>", methods=["GET", "POST"])
@login_required(role="admin")
def admin_edit(idx):
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
        flash("Đã cập nhật thành công.")
        return redirect(url_for("admin_database", type=dtype))
    return render_template("admin_edit.html", idx=idx, chunk=chunk, dtype=dtype, data_types=DATA_TYPES)

@app.route("/admin/delete/<int:idx>", methods=["POST"])
@login_required(role="admin")
def admin_delete(idx):
    dtype = request.args.get("type", DEFAULT_TYPE)
    if dtype not in DATA_TYPES: dtype = DEFAULT_TYPE
    chunks = load_chunks(dtype)
    if idx < 0 or idx >= len(chunks):
        return "Không tìm thấy mục!", 404
    chunks.pop(idx)
    save_chunks(dtype, chunks)
    flash("Đã xóa mục kiến thức.")
    return redirect(url_for("admin_database", type=dtype))

#======== xử lý cache chat history ====
@app.route("/admin/cache/delete/<int:idx>", methods=["POST"])
def admin_cache_delete(idx):
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login"))
    cache = load_chat_history()
    if 0 <= idx < len(cache):
        cache.pop(idx)
        save_chat_history(cache)
        flash("Đã xóa câu hỏi khỏi cache!")
    return redirect(url_for("admin_dashboard", tab="cache"))

@app.route("/admin/cache/clear", methods=["POST"])
def admin_cache_clear():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login"))
    save_chat_history([])
    flash("Đã xóa toàn bộ cache!")
    return redirect(url_for("admin_dashboard", tab="cache"))
#======== xử lý rule_based ====
@app.route("/admin/add_rule", methods=["POST"])
def admin_add_rule():    
    intent = request.form["intent"]
    patterns = [p.strip() for p in request.form["patterns"].split(",")]
    response = request.form["response"]

    rules = load_rules()
    rules.append({"intent": intent, "patterns": patterns, "response": response})
    with open(RULE_PATH, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)

    return redirect(url_for("admin_dashboard", tab="rules"))


@app.route("/admin/delete_rule", methods=["POST"])
def admin_delete_rule():
    index = int(request.args.get("index"))
    rules = load_rules()
    if 0 <= index < len(rules):
        del rules[index]
        with open(RULE_PATH, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
    return redirect(url_for("admin_dashboard", tab="rules"))

if __name__ == "__main__":
    app.run(debug=True)
