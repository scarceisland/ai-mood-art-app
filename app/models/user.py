import os
import json
from typing import Dict, List
from werkzeug.security import check_password_hash, generate_password_hash
from json import JSONDecodeError

# Public constant used by templates/routes
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin").lower()

ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")
ADMIN_PASSWORD_PLAIN = os.getenv("ADMIN_PASSWORD")
USERS_FILE_ENV = os.getenv("USERS_JSON", "users.json")
ADMIN_PWD_HASH_FILE = "admin_pwd.hash"

# In-memory cache for user credentials
_USERS_CACHE: Dict[str, str] = {}


def _possible_user_paths() -> List[str]:
    """Generates a list of possible paths for the users.json file."""
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(here, "..", ".."))
    return [
        os.path.join(project_root, "data", "users.json"),
        os.path.join(project_root, USERS_FILE_ENV),
    ]


def _load_users_from_file() -> Dict[str, str]:
    """Load users from a JSON file. Returns {} if not found or invalid."""
    for path in _possible_user_paths():
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                records = json.load(f)
            if not isinstance(records, list):
                continue

            result = {}
            for rec in records:
                if isinstance(rec, dict):
                    u = rec.get("username")
                    h = rec.get("password_hash")
                    if isinstance(u, str) and isinstance(h, str):
                        result[u.strip().lower()] = h
            return result
        except (JSONDecodeError, TypeError, IOError):
            continue
    return {}


def _fallback_env_user() -> Dict[str, str]:
    """Create a single admin user from env vars or a hash file."""
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(here, "..", ".."))
    hash_file_path = os.path.join(project_root, ADMIN_PWD_HASH_FILE)

    if os.path.exists(hash_file_path):
        with open(hash_file_path, "r", encoding="utf-8") as f:
            return {ADMIN_USERNAME: f.read().strip()}

    if ADMIN_PASSWORD_HASH:
        return {ADMIN_USERNAME: ADMIN_PASSWORD_HASH}
    if ADMIN_PASSWORD_PLAIN:
        return {ADMIN_USERNAME: generate_password_hash(ADMIN_PASSWORD_PLAIN)}
    # Development-only default password
    return {ADMIN_USERNAME: generate_password_hash("admin123")}


def _ensure_users_loaded() -> None:
    """Loads users into the cache if it's empty."""
    global _USERS_CACHE
    if _USERS_CACHE:
        return

    # Load file users and merge with the admin user config to ensure admin always exists.
    users = _load_users_from_file()
    users.update(_fallback_env_user())
    _USERS_CACHE = users


def refresh_users_cache() -> None:
    """Clears and reloads the user cache from source."""
    global _USERS_CACHE
    _USERS_CACHE = {}
    _ensure_users_loaded()


def verify_credentials(username: str, password: str) -> bool:
    """Return True when username exists and password matches (case-insensitive username)."""
    _ensure_users_loaded()
    uname = (username or "").strip().lower()

    if not uname or not password:
        return False

    stored_hash = _USERS_CACHE.get(uname)
    if not stored_hash:
        return False

    try:
        return check_password_hash(stored_hash, password)
    except (TypeError, ValueError):
        return False


def delete_user_data(username: str, db_conn) -> bool:
    """
    Deletes a user from the users.json file and all their associated data
    from the feedback and logs tables in the database.
    """
    uname_lower = username.lower()
    if uname_lower == ADMIN_USERNAME:
        return False

    # 1. Remove user from the users.json file
    user_file_path = next((path for path in _possible_user_paths() if os.path.exists(path)), None)

    if user_file_path:
        with open(user_file_path, "r", encoding="utf-8") as f:
            users = json.load(f)

        users_after_deletion = [
            user for user in users
            if user.get("username", "").lower() != uname_lower
        ]

        with open(user_file_path, "w", encoding="utf-8") as f:
            json.dump(users_after_deletion, f, indent=2)

    # 2. Delete user data from the database
    try:
        db_conn.execute("DELETE FROM feedback WHERE username = ?", (username,))
        db_conn.execute("DELETE FROM logs WHERE user = ?", (username,))
        db_conn.commit()
    except Exception:
        # If the database operation fails, the deletion is not successful.
        return False

    # 3. Refresh the in-memory cache to reflect the deletion
    refresh_users_cache()

    return True

