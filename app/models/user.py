# user.py
import psycopg2
from psycopg2 import pool, sql
from werkzeug.security import generate_password_hash, check_password_hash

# Database connection parameters
DB_CONFIG = {
    'dbname': 'your_db_name',
    'user': 'your_db_user',
    'password': 'your_db_password',
    'host': 'localhost',
    'port': '5432',
}

# Initialize connection pool
connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 10,  # minconn, maxconn
    **DB_CONFIG
)


class PooledConnection:
    """Context manager for psycopg2 connection pooling."""

    def __enter__(self):
        self.conn = connection_pool.getconn()
        self.cur = self.conn.cursor()
        return self.cur

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.cur.close()
        connection_pool.putconn(self.conn)


class User:
    """
    User model with full CRUD, search/filter, pagination, total count,
    and bulk creation using psycopg2 connection pooling.
    """

    def __init__(self, id=None, username=None, email=None, password_hash=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

    @classmethod
    def create_table(cls):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(150) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL
        );
        """
        with PooledConnection() as cur:
            cur.execute(query)

    @classmethod
    def create(cls, username, email, password):
        password_hash = generate_password_hash(password)
        query = """
        INSERT INTO users (username, email, password_hash)
        VALUES (%s, %s, %s)
        RETURNING id;
        """
        with PooledConnection() as cur:
            cur.execute(query, (username, email, password_hash))
            user_id = cur.fetchone()[0]
        return cls(id=user_id, username=username, email=email, password_hash=password_hash)

    @classmethod
    def bulk_create(cls, users):
        """
        Bulk create multiple users.
        users: list of dicts with keys 'username', 'email', 'password'
        Example:
            users = [
                {"username": "john", "email": "john@example.com", "password": "1234"},
                {"username": "jane", "email": "jane@example.com", "password": "abcd"}
            ]
            User.bulk_create(users)
        """
        if not users:
            return []

        # Hash passwords and prepare values
        values = [(u['username'], u['email'], generate_password_hash(u['password'])) for u in users]

        query = sql.SQL(
            "INSERT INTO users (username, email, password_hash) VALUES {} RETURNING id, username, email, password_hash").format(
            sql.SQL(',').join(sql.Placeholder() * len(values))
        )

        # Flatten the list of tuples for psycopg2 execute
        flattened_values = [item for sublist in values for item in sublist]

        with PooledConnection() as cur:
            psycopg2.extras.execute_values(
                cur,
                "INSERT INTO users (username, email, password_hash) VALUES %s RETURNING id, username, email, password_hash;",
                values,
                template=None,
                page_size=100
            )
            created_users = [cls(*row) for row in cur.fetchall()]

        return created_users

    @classmethod
    def get_by_id(cls, user_id):
        query = "SELECT id, username, email, password_hash FROM users WHERE id = %s;"
        with PooledConnection() as cur:
            cur.execute(query, (user_id,))
            row = cur.fetchone()
        if row:
            return cls(*row)
        return None

    @classmethod
    def get_by_username(cls, username):
        query = "SELECT id, username, email, password_hash FROM users WHERE username = %s;"
        with PooledConnection() as cur:
            cur.execute(query, (username,))
            row = cur.fetchone()
        if row:
            return cls(*row)
        return None

    @classmethod
    def search_by_email(cls, email_partial, page=1, per_page=10):
        offset = (page - 1) * per_page
        query = "SELECT id, username, email, password_hash FROM users WHERE email ILIKE %s ORDER BY id LIMIT %s OFFSET %s;"
        like_pattern = f"%{email_partial}%"
        with PooledConnection() as cur:
            cur.execute(query, (like_pattern, per_page, offset))
            rows = cur.fetchall()
        return [cls(*row) for row in rows]

    @classmethod
    def filter(cls, page=1, per_page=10, **kwargs):
        offset = (page - 1) * per_page
        if not kwargs:
            return cls.get_all(page=page, per_page=per_page)

        conditions = []
        params = []
        for key, value in kwargs.items():
            conditions.append(f"{key} ILIKE %s")
            params.append(f"%{value}%")

        query = f"SELECT id, username, email, password_hash FROM users WHERE {' AND '.join(conditions)} ORDER BY id LIMIT %s OFFSET %s;"
        params.extend([per_page, offset])
        with PooledConnection() as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
        return [cls(*row) for row in rows]

    @classmethod
    def get_all(cls, page=1, per_page=10):
        offset = (page - 1) * per_page
        query = "SELECT id, username, email, password_hash FROM users ORDER BY id LIMIT %s OFFSET %s;"
        with PooledConnection() as cur:
            cur.execute(query, (per_page, offset))
            rows = cur.fetchall()
        return [cls(*row) for row in rows]

    @classmethod
    def count(cls, **kwargs):
        if not kwargs:
            query = "SELECT COUNT(*) FROM users;"
            params = ()
        else:
            conditions = []
            params = []
            for key, value in kwargs.items():
                conditions.append(f"{key} ILIKE %s")
                params.append(f"%{value}%")
            query = f"SELECT COUNT(*) FROM users WHERE {' AND '.join(conditions)};"

        with PooledConnection() as cur:
            cur.execute(query, tuple(params))
            total = cur.fetchone()[0]
        return total

    def update(self, username=None, email=None, password=None):
        updates = []
        params = []

        if username:
            updates.append("username = %s")
            params.append(username)
        if email:
            updates.append("email = %s")
            params.append(email)
        if password:
            updates.append("password_hash = %s")
            params.append(generate_password_hash(password))

        if not updates:
            return False

        params.append(self.id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s;"
        with PooledConnection() as cur:
            cur.execute(query, tuple(params))
        return True

    def delete(self):
        query = "DELETE FROM users WHERE id = %s;"
        with PooledConnection() as cur:
            cur.execute(query, (self.id,))
        return True

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
