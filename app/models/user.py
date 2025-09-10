from werkzeug.security import check_password_hash, generate_password_hash
from app.db import db


class User(db.Model):
    """
    Represents a user in the database.
    """
    # This sets the table name in PostgreSQL
    __tablename__ = 'users'

    # Defines the columns for the 'users' table
    # 'id' will become 'SERIAL PRIMARY KEY' in PostgreSQL
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        """Hashes and sets the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


# --- Helper Functions to Replace Old Logic ---

def verify_credentials(username: str, password: str) -> bool:
    """
    Verifies user credentials against the database.
    This is a case-insensitive username check.
    """
    if not username or not password:
        return False

    # Query the database for the user
    user = User.query.filter(db.func.lower(User.username) == db.func.lower(username)).first()

    # If user exists and password is correct, return True
    if user and user.check_password(password):
        return True

    return False


def get_user(username: str) -> User | None:
    """Gets a user by username (case-insensitive)."""
    return User.query.filter(db.func.lower(User.username) == db.func.lower(username)).first()


def delete_user(username: str) -> bool:
    """
    Deletes a user from the database. Protects the 'admin' user.
    Note: Deleting related feedback/logs should be handled in the route.
    """
    user = get_user(username)
    # Prevent the admin user from being deleted
    if user and user.username.lower() != 'admin':
        db.session.delete(user)
        db.session.commit()
        return True
    return False
