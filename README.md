# Expense Tracker Server

This project is an expense tracking backend built with FastAPI, JWT authentication, OAuth2-style password flow, and FastMCP tools.

## What this project does

The server lets you:
- register a user account
- log in securely
- receive a JWT access token
- access protected expense APIs
- add, view, update, and delete expenses
- summarize expenses by category

## Main files

- [main.py](main.py) - main FastAPI + FastMCP server with auth and expense tools
- [main2.py](main2.py) - alternate server entrypoint with the same auth and expense logic
- [categories.json](categories.json) - default expense categories
- [requirements.txt](requirements.txt) - Python dependencies
- [pyproject.toml](pyproject.toml) - project metadata and dependency list

## Requirements

- Python 3.11+
- MySQL server
- A virtual environment is recommended

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment variables

Set these before starting the server:

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=""
export MYSQL_DATABASE=expenses_db
export JWT_SECRET_KEY="your-secret"
export JWT_ALGORITHM=HS256
export JWT_EXPIRE_MINUTES=30
export PORT=8000
```

The app will create the database and required tables automatically if they do not exist.

## Run the server

```bash
./.venv/bin/python main.py
```

The server starts on port 8000 by default and listens on `0.0.0.0`.

## Authentication flow

### Login

Send a request to:

```bash
POST /token
```

Use form data:

```text
username=your_username
password=your_password
```

Example response:

```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer"
}
```

### Protected route

Use the token in the Authorization header:

```text
Authorization: Bearer <access_token>
```

The `/me` route returns the authenticated user info for the current token.

## MCP tools

The server also exposes MCP tools such as:

- `register_user(username, password, email="")`
- `login_user(username, password)`
- `add_expense(token, date, amount, category, subcategory="", note="")`
- `list_expenses(token, start_date, end_date)`
- `summarize(token, start_date, end_date, category=None)`
- `update_expense(token, expense_id, ...)`
- `delete_expense(token, expense_id)`

## Example usage

### Register user

```bash
curl -X POST "http://localhost:8000/register_user" \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"Demo@123","email":"demo@example.com"}'
```

### Login

```bash
curl -X POST "http://localhost:8000/token" \
  -d "username=demo&password=Demo@123"
```

### Add expense

```bash
curl -X POST "http://localhost:8000/add_expense" \
  -H "Authorization: Bearer <token>" \
  -d "date=2026-08-02&amount=250&category=Food"
```

## Password handling note

Passwords are normalized before hashing and stored in the `users.password_hash` column. The schema is widened to `VARCHAR(512)` so bcrypt hashes can be stored safely without truncation issues.

## Summary

This project combines FastAPI, JWT, FastMCP tools, and MySQL to build a secure expense tracking backend.
