# models/user.py
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

# Cache: username(lowercased) -> password_hash
_USERS_CACHE: Dict[str, str] = {}


def _possible_user_paths() -> List[str]:
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(here, ".."))
    return [
        os.path.join(here, USERS_FILE_ENV),                 # models/users.json
        os.path.join(project_root, "data", "users.json"),   # project_root/data/users.json
        os.path.join(project_root, USERS_FILE_ENV),         # project_root/users.json
    ]


def _load_users_from_file() -> Dict[str, str]:
    """Load users from a JSON file. Returns {} if not found/invalid."""
    for path in _possible_user_paths():
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except (JSONDecodeError, TypeError):
                continue
            if not isinstance(data, list):
                continue
            result = {}
            for rec in data:
                if not isinstance(rec, dict):
                    continue
                u = rec.get("username")
                h = rec.get("password_hash")
                if isinstance(u, str) and isinstance(h, str):
                    result[u.strip().lower()] = h
        if result:
            return result
    return {}


def _fallback_env_user() -> Dict[str, str]:
    """Create a single admin user from env for local/dev."""
    if ADMIN_PASSWORD_HASH:
        return {ADMIN_USERNAME: ADMIN_PASSWORD_HASH}
    if ADMIN_PASSWORD_PLAIN:
        return {ADMIN_USERNAME: generate_password_hash(ADMIN_PASSWORD_PLAIN)}
    # dev-only default
    return {ADMIN_USERNAME: generate_password_hash("admin")}


def _ensure_users_loaded() -> None:
    """
    Loads users from the JSON file and merges the admin user from environment variables.
    """
    global _USERS_CACHE
    if _USERS_CACHE:
        return

    # --- FIX START ---
    # The original code only loaded the admin user if the users.json file was empty.
    # The corrected logic loads users from the file first, then updates the dictionary
    # with the admin user from the environment, ensuring the admin is always present.

    # 1. Load standard users from the JSON file.
    users = _load_users_from_file()

    # 2. Load the admin user from environment variables.
    admin_user = _fallback_env_user()

    # 3. Merge the admin user into the main user dictionary.
    #    This adds the admin or overwrites it if it was in the file.
    users.update(admin_user)

    _USERS_CACHE = users
    # --- FIX END ---


def refresh_users_cache() -> None:
    global _USERS_CACHE
    _USERS_CACHE = {}
    _ensure_users_loaded()


def verify_credentials(username: str, password: str) -> bool:
    """Return True when username exists and password matches (case-insensitive username)."""
    _ensure_users_loaded()
    uname = (username or "").strip().lower()
    stored_hash = _USERS_CACHE.get(uname)

    if not stored_hash:
        return False

    try:
        return check_password_hash(stored_hash, password or "")
    except TypeError:
        # In case of bad hash data
        return False
