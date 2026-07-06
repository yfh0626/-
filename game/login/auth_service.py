import os
import json
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

class AuthService:
    DB_PATH = "login/users.json"
    KEY_PATH = "login/key.key"

    def __init__(self):
        os.makedirs("login/avatars", exist_ok=True)
        if not os.path.exists(self.DB_PATH):
            with open(self.DB_PATH, "w") as f: json.dump({"users": {}, "remember_me": None}, f)
        
        # 加载或生成密钥
        if not os.path.exists(self.KEY_PATH):
            key = Fernet.generate_key()
            with open(self.KEY_PATH, "wb") as f: f.write(key)
        with open(self.KEY_PATH, "rb") as f:
            self.fernet = Fernet(f.read())

    def hash_password(self, password: str, salt: bytes = None) -> tuple[bytes, bytes]:
        salt = salt or os.urandom(16)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
        return kdf.derive(password.encode()), salt

    def verify_password(self, input_password, stored_hash, stored_salt) -> bool:
        new_hash, _ = self.hash_password(input_password, salt=stored_salt)
        return new_hash == stored_hash

    def save_user(self, username, password, avatar_path):
        hash_val, salt = self.hash_password(password)
        data = self.load_db()
        data["users"][username] = {
            "hash": base64.b64encode(hash_val).decode(),
            "salt": base64.b64encode(salt).decode(),
            "encrypted_pass": self.fernet.encrypt(password.encode()).decode(),
            "avatar": avatar_path,
            "wins": 0,
            "total_games": 0,
        }
        with open(self.DB_PATH, "w") as f: json.dump(data, f, indent=4)

    def get_user_stats(self, username):
        data = self.load_db()
        user = data["users"].get(username)
        if user is None:
            return None
        return {"wins": user.get("wins", 0), "total_games": user.get("total_games", 0)}

    def get_user_avatar(self, username):
        data = self.load_db()
        user = data["users"].get(username)
        if user is None:
            return None
        return user.get("avatar", None)

    def save_last_lineup(self, username, hero_id, skill_ids):
        data = self.load_db()
        user = data["users"].get(username)
        if user is None:
            return
        user["last_hero"] = hero_id
        user["last_skills"] = list(skill_ids)
        with open(self.DB_PATH, "w") as f: json.dump(data, f, indent=4)

    def get_last_lineup(self, username):
        data = self.load_db()
        user = data["users"].get(username)
        if user is None:
            return None
        return {
            "hero": user.get("last_hero"),
            "skills": user.get("last_skills"),
        }

    def add_game_result(self, username, won: bool):
        data = self.load_db()
        user = data["users"].get(username)
        if user is None:
            return
        user.setdefault("wins", 0)
        user.setdefault("total_games", 0)
        user["total_games"] += 1
        if won:
            user["wins"] += 1
        with open(self.DB_PATH, "w") as f: json.dump(data, f, indent=4)

    def load_db(self):
        with open(self.DB_PATH, "r") as f: return json.load(f)