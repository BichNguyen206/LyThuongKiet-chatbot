import os
import hashlib
import json

# Xác định đường dẫn tuyệt đối tới file users.json (từ gốc project)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_FILE = os.path.join(BASE_DIR, "data", "users.json")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password, role, fullname, class_name=None, email=None):
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    else:
        users = []
    if any(u["username"] == username for u in users):
        raise Exception("Username đã tồn tại!")
    user = {
        "user_id": str(len(users) + 1),
        "username": username,
        "password_hash": hash_password(password),
        "role": role,
        "fullname": fullname,
    }
    if class_name:
        user["class"] = class_name
    if email:
        user["email"] = email
    users.append(user)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def check_login(username, password):
    if not os.path.exists(USERS_FILE):
        print("Không tìm thấy file users.json!")
        return None
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
    input_hash = hash_password(password)
    print(f"Bạn nhập: {username=} {password=}, hash={input_hash}")
    for user in users:
        print(f"Kiểm tra với: {user['username']=}, {user['password_hash']=}")
        if user["username"] == username and user["password_hash"] == input_hash:
            print(">>> Đăng nhập thành công!")
            return user
    print(">>> Đăng nhập thất bại!")
    return None
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
    return users

def save_users(users, path='data/users.json'):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)
