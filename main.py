import asyncio
import hashlib
import os

from fastmcp import FastMCP
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")


def _get_env(*names, default=None):
    for name in names:
        value = os.getenv(name)
        if value not in (None, ""):
            return value
    return default


DB_CONFIG = {
    "host": _get_env("MYSQL_HOST", "MYSQLHOST", default="localhost"),
    "port": int(_get_env("MYSQL_PORT", "MYSQLPORT", default="3306")),
    "user": _get_env("MYSQL_USER", "MYSQLUSER", default="root"),
    "password": _get_env("MYSQL_PASSWORD", "MYSQLPASSWORD", default=""),
    "database": _get_env("MYSQL_DATABASE", "MYSQLDATABASE", default="expenses_db"),
    "autocommit": True,
}

mcp = FastMCP("ExpenseTracker")


def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as exc:
        print(f"MySQL connection failed: {exc}")
        return None


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _get_user_by_username(username):
    conn = get_connection()
    if conn is None:
        return None

    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT id, username, password_hash FROM users WHERE username = %s",
                (username,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def _authenticate_user(username, password):
    user = _get_user_by_username(username)
    if not user:
        return None

    if user["password_hash"] != _hash_password(password):
        return None

    return user


def init_db():
    try:
        init_conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            autocommit=True,
        )
    except mysql.connector.Error as exc:
        print(f"MySQL init failed: {exc}")
        return

    try:
        with init_conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}`")
    finally:
        init_conn.close()

    conn = get_connection()
    if conn is None:
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(255) NOT NULL DEFAULT '',
                    password_hash VARCHAR(255) NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT DEFAULT NULL,
                    date VARCHAR(20) NOT NULL,
                    amount DOUBLE NOT NULL,
                    category VARCHAR(255) NOT NULL,
                    subcategory VARCHAR(255) DEFAULT '',
                    note TEXT,
                    CONSTRAINT fk_expenses_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute("SHOW COLUMNS FROM expenses LIKE 'user_id'")
            if cursor.fetchone() is None:
                cursor.execute("ALTER TABLE expenses ADD COLUMN user_id INT DEFAULT NULL")
    finally:
        conn.close()


async def initialize_app():
    await asyncio.to_thread(init_db)


@mcp.tool()
def register_user(username, password, email=""):
    """Create a new user account for the expense tracker."""
    if not username or not password:
        return {"status": "error", "message": "Username and password are required"}

    conn = get_connection()
    if conn is None:
        return {"status": "error", "message": "MySQL connection is unavailable"}

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return {"status": "error", "message": "Username already exists"}

            cur.execute(
                "INSERT INTO users(username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, _hash_password(password)),
            )
            return {"status": "ok", "user_id": cur.lastrowid, "username": username}
    finally:
        conn.close()


@mcp.tool()
def login_user(username, password):
    """Authenticate a user and return their user id."""
    user = _authenticate_user(username, password)
    if not user:
        return {"status": "error", "message": "Invalid username or password"}

    return {"status": "ok", "user_id": user["id"], "username": user["username"]}


@mcp.tool()
def add_expense(user_id, date, amount, category, subcategory="", note=""):
    """Add a new expense entry for the authenticated user."""
    if not user_id:
        return {"status": "error", "message": "A valid user_id is required"}

    conn = get_connection()
    if conn is None:
        return {"status": "error", "message": "MySQL connection is unavailable"}

    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO expenses(user_id, date, amount, category, subcategory, note) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, date, amount, category, subcategory, note),
            )
            return {"status": "ok", "id": cur.lastrowid}
    finally:
        conn.close()


@mcp.tool()
def list_expenses(user_id, start_date, end_date):
    """List expense entries for a specific user within an inclusive date range."""
    conn = get_connection()
    if conn is None:
        return {"status": "error", "message": "MySQL connection is unavailable"}

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE user_id = %s AND date BETWEEN %s AND %s
                ORDER BY id ASC
                """,
                (user_id, start_date, end_date),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()


@mcp.tool()
def summarize(user_id, start_date, end_date, category=None):
    """Summarize expenses for a specific user within an inclusive date range."""
    conn = get_connection()
    if conn is None:
        return {"status": "error", "message": "MySQL connection is unavailable"}

    try:
        with conn.cursor() as cur:
            query = """
                SELECT category, SUM(amount) AS total_amount
                FROM expenses
                WHERE user_id = %s AND date BETWEEN %s AND %s
            """
            params = [user_id, start_date, end_date]

            if category:
                query += " AND category = %s"
                params.append(category)

            query += " GROUP BY category ORDER BY category ASC"

            cur.execute(query, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()


@mcp.tool()
def update_expense(user_id, expense_id, date=None, amount=None, category=None, subcategory=None, note=None):
    """Update an existing expense entry for the authenticated user."""
    if not any(value is not None for value in [date, amount, category, subcategory, note]):
        return {"status": "error", "message": "No fields provided to update"}

    conn = get_connection()
    if conn is None:
        return {"status": "error", "message": "MySQL connection is unavailable"}

    try:
        with conn.cursor() as cur:
            fields = []
            values = []

            if date is not None:
                fields.append("date = %s")
                values.append(date)
            if amount is not None:
                fields.append("amount = %s")
                values.append(amount)
            if category is not None:
                fields.append("category = %s")
                values.append(category)
            if subcategory is not None:
                fields.append("subcategory = %s")
                values.append(subcategory)
            if note is not None:
                fields.append("note = %s")
                values.append(note)

            values.extend([expense_id, user_id])
            cur.execute(
                f"UPDATE expenses SET {', '.join(fields)} WHERE id = %s AND user_id = %s",
                values,
            )
            return {"status": "ok", "updated_rows": cur.rowcount}
    finally:
        conn.close()


@mcp.tool()
def delete_expense(user_id, expense_id):
    """Delete an expense entry for the authenticated user."""
    conn = get_connection()
    if conn is None:
        return {"status": "error", "message": "MySQL connection is unavailable"}

    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM expenses WHERE id = %s AND user_id = %s", (expense_id, user_id))
            return {"status": "ok", "deleted_rows": cur.rowcount}
    finally:
        conn.close()


@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    # Read fresh each time so you can edit the file without restarting
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    asyncio.run(initialize_app())
    mcp.run(transport="http", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
