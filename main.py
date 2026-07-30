import asyncio
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
                CREATE TABLE IF NOT EXISTS expenses(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date VARCHAR(20) NOT NULL,
                    amount DOUBLE NOT NULL,
                    category VARCHAR(255) NOT NULL,
                    subcategory VARCHAR(255) DEFAULT '',
                    note TEXT
                )
                """
            )
    finally:
        conn.close()


async def initialize_app():
    await asyncio.to_thread(init_db)


@mcp.tool()
def add_expense(date, amount, category, subcategory="", note=""):
    """Add a new expense entry to the database."""
    conn = get_connection()
    if conn is None:
        return {"status": "error", "message": "MySQL connection is unavailable"}

    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (%s, %s, %s, %s, %s)",
                (date, amount, category, subcategory, note),
            )
            return {"status": "ok", "id": cur.lastrowid}
    finally:
        conn.close()


@mcp.tool()
def list_expenses(start_date, end_date):
    """List expense entries within an inclusive date range."""
    conn = get_connection()
    if conn is None:
        return {"status": "error", "message": "MySQL connection is unavailable"}

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN %s AND %s
                ORDER BY id ASC
                """,
                (start_date, end_date),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()


@mcp.tool()
def summarize(start_date, end_date, category=None):
    """Summarize expenses by category within an inclusive date range."""
    conn = get_connection()
    if conn is None:
        return {"status": "error", "message": "MySQL connection is unavailable"}

    try:
        with conn.cursor() as cur:
            query = """
                SELECT category, SUM(amount) AS total_amount
                FROM expenses
                WHERE date BETWEEN %s AND %s
            """
            params = [start_date, end_date]

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
def update_expense(expense_id, date=None, amount=None, category=None, subcategory=None, note=None):
    """Update an existing expense entry by id."""
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

            values.append(expense_id)
            cur.execute(f"UPDATE expenses SET {', '.join(fields)} WHERE id = %s", values)
            return {"status": "ok", "updated_rows": cur.rowcount}
    finally:
        conn.close()


@mcp.tool()
def delete_expense(expense_id):
    """Delete an expense entry by id."""
    conn = get_connection()
    if conn is None:
        return {"status": "error", "message": "MySQL connection is unavailable"}

    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
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
