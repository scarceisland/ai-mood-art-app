# add_users.py
import os
import json
from werkzeug.security import generate_password_hash

# Path to your users.json file
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
data_dir = os.path.join(project_root, "data")
users_path = os.path.join(data_dir, "users.json")

# Ensure data directory exists
os.makedirs(data_dir, exist_ok=True)

# Current users (including the new ones)
users = {
    "paul": "paul123",
    "sarah": "sarah123",
    "john": "john123",
    "dana": "dana123",
    "eric": "eric123",
    "fran": "fran123",
    "guest": "guest123",
    "mike": "mike123",
    "lisa": "lisa123",
    "tom": "tom123"
}

# Load existing users if file exists
existing_users = []
if os.path.exists(users_path):
    with open(users_path, "r") as f:
        existing_users = json.load(f)

# Create a set of existing usernames for quick lookup
existing_usernames = {user["username"] for user in existing_users}

# Add new users that don't exist yet
for username, password in users.items():
    if username not in existing_usernames:
        existing_users.append({
            "username": username,
            "password_hash": generate_password_hash(password)
        })
        print(f"Added user: {username}")

# Save updated user list
with open(users_path, "w") as f:
    json.dump(existing_users, f, indent=2)

print("User database updated successfully!")