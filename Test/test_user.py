
from src.user_utils import add_user
import os
import sys
from dotenv import load_dotenv
import openai
# Thêm đường dẫn src để import rag_retrieve.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
add_user("admin", "123456", "admin", "Quản trị viên")
