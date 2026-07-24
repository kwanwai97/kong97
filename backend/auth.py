"""
Auth module - simple token-based auth for development.
Production: replace with bcrypt + JWT + https.
"""
import json
import os
import secrets
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
USERS_FILE = BASE / "data" / "users.json"
SESSIONS_FILE = BASE / "data" / "sessions.json"


def _load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def register(username, password, display_name=""):
    users = _load_json(USERS_FILE, {})
    if username in users:
        return {"ok": False, "error": "用戶名已存在"}
    uid = secrets.token_hex(8)
    users[username] = {
        "id": uid,
        "password_hash": password,  # plain for dev only
        "display_name": display_name or username,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "last_login": None,
    }
    _save_json(USERS_FILE, users)
    return {"ok": True, "user_id": uid, "username": username, "display_name": display_name or username}


def login(username, password):
    users = _load_json(USERS_FILE, {})
    u = users.get(username)
    if not u or u.get("password_hash") != password:
        return {"ok": False, "error": "帳號或密碼錯誤"}
    u["last_login"] = datetime.utcnow().isoformat() + "Z"
    _save_json(USERS_FILE, users)
    token = secrets.token_hex(16)
    sessions = _load_json(SESSIONS_FILE, {})
    sessions[token] = {"user_id": u["id"], "username": username, "created_at": datetime.utcnow().isoformat() + "Z"}
    _save_json(SESSIONS_FILE, sessions)
    return {"ok": True, "token": token, "user_id": u["id"], "username": username, "display_name": u.get("display_name", username)}


def verify(token):
    sessions = _load_json(SESSIONS_FILE, {})
    s = sessions.get(token)
    if not s:
        return None
    return {"user_id": s["user_id"], "username": s["username"]}


def get_user(user_id):
    users = _load_json(USERS_FILE, {})
    for u in users.values():
        if u.get("id") == user_id:
            return u
    return None
