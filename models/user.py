import os
from werkzeug.security import generate_password_hash, check_password_hash

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ADMIN_HASH_PATH = os.path.join(DATA_DIR, "admin_pwd.hash")

ADMIN_USERNAME = "admin"

def _initial_admin_password():
    # Read a plain admin password from env (for first run only)
    return os.getenv("ADMIN_PASSWORD", "admin123")

def _read_admin_hash_from_file():
    if os.path.exists(ADMIN_HASH_PATH):
        with open(ADMIN_HASH_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

# Load or create admin hash
ADMIN_HASH = _read_admin_hash_from_file()
if not ADMIN_HASH:
    os.makedirs(DATA_DIR, exist_ok=True)
    ADMIN_HASH = generate_password_hash(_initial_admin_password())
    with open(ADMIN_HASH_PATH, "w", encoding="utf-8") as f:
        f.write(ADMIN_HASH)

# Build demo users (hashed)
USERS = {}

def _rebuild_users():
    global USERS
    USERS = {ADMIN_USERNAME: ADMIN_HASH}
    for i in range(1, 10):
        USERS[f"user{i}"] = generate_password_hash(f"pass{i}")

_rebuild_users()

def verify_credentials(username: str, password: str) -> bool:
    hash_ = USERS.get(username)
    if not hash_:
        return False
    return check_password_hash(hash_, password)

def set_admin_password(new_plain: str):
    """Update admin hash on disk and in-memory."""
    global ADMIN_HASH
    ADMIN_HASH = generate_password_hash(new_plain)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ADMIN_HASH_PATH, "w", encoding="utf-8") as f:
        f.write(ADMIN_HASH)
    _rebuild_users()
    return True
