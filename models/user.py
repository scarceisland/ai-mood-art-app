from werkzeug.security import generate_password_hash

USERS = {"admin": generate_password_hash("admin123")}
for i in range(1, 10):
    USERS[f"user{i}"] = generate_password_hash(f"pass{i}")

ADMIN_USERNAME = "admin"
