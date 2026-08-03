# Expenses MCP Server

A production-ready **Model Context Protocol (MCP)** server that enables AI assistants to securely manage personal expenses through natural language. The server uses **Auth0 OAuth 2.0**, **JWT authentication**, **FastMCP**, and **MySQL** to provide secure, user-specific expense management for MCP-compatible clients such as Claude Desktop.

---

## Overview

Expenses MCP Server exposes a collection of MCP tools that allow AI assistants to perform expense management operations on behalf of authenticated users. Each request is authorized using JWT tokens issued by Auth0, ensuring that users can only access their own financial data.

This project demonstrates how to build a secure, remote MCP server following modern authentication and backend development practices.

---

## Features

- Secure user authentication with Auth0 OAuth 2.0
- JWT-based authorization
- User registration and login
- Add new expenses
- View expense history
- Update existing expenses
- Delete expenses
- Expense categorization
- MySQL database integration
- Remote MCP server deployment
- Compatible with Claude Desktop and other MCP clients
- Environment-based configuration
- Production-ready architecture

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend Development |
| FastMCP | MCP Server Framework |
| FastAPI | HTTP Server |
| Auth0 | Authentication Provider |
| JWT | Authorization |
| MySQL | Database |
| Uvicorn | ASGI Server |
| python-dotenv | Environment Management |

---

## Architecture

```
                ┌────────────────────────────┐
                │      MCP Client            │
                │ (Claude Desktop, etc.)     │
                └─────────────┬──────────────┘
                              │
                       OAuth Authentication
                              │
                              ▼
                     Auth0 Authorization
                              │
                     JWT Access Token
                              │
                              ▼
                 Expenses MCP Server (FastMCP)
                              │
                 JWT Verification Middleware
                              │
                    Business Logic & Tools
                              │
                              ▼
                        MySQL Database
```

---

## Project Structure

```
Expenses-MCP-Server/
│
├── main.py
├── auth.py
├── database.py
├── categories.json
├── requirements.txt
├── .env
├── README.md
```

---

## Installation

### Clone the repository

```bash
git clone https://github.com/nikhil2005verma/Expenses-MCP-Server.git
cd Expenses-MCP-Server
```

### Create a virtual environment

```bash
python -m venv .venv
```

### Activate the environment

**Windows**

```bash
.venv\Scripts\activate
```

**Linux/macOS**

```bash
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file and configure the following variables.

```env
DB_HOST=
DB_PORT=
DB_USER=
DB_PASSWORD=
DB_NAME=

AUTH0_DOMAIN=
AUTH0_AUDIENCE=
AUTH0_CLIENT_ID=
AUTH0_CLIENT_SECRET=
AUTH0_ISSUER=

JWT_SECRET=
```

---

## Running the Server

```bash
python main.py
```

or

```bash
uvicorn main:app --reload
```

---

## Available MCP Tools

| Tool | Description |
|------|-------------|
| register_user | Register a new user |
| login_user | Authenticate a user |
| add_expense | Add a new expense |
| get_expenses | Retrieve user expenses |
| update_expense | Update an expense |
| delete_expense | Delete an expense |
| expense_summary | Generate an expense summary |

---

## Authentication Flow

1. User authenticates through Auth0.
2. Auth0 issues a JWT access token.
3. The MCP client includes the token with each request.
4. The server validates the JWT.
5. User identity is extracted from the token.
6. Only the authenticated user's data is accessed.

---

## Security Features

- OAuth 2.0 Authentication
- JWT Access Token Validation
- User-specific Data Isolation
- Protected MCP Tools
- Environment Variable Configuration
- Secure Database Integration

---

## Deployment

The project can be deployed to any platform that supports Python ASGI applications, including:

- Railway
- Render
- Fly.io
- Docker
- VPS
- FastMCP Cloud

---

## Future Enhancements

- Budget management
- Monthly analytics
- Spending insights
- CSV export
- PDF reports
- Multi-currency support
- Recurring expenses
- Email notifications
- AI-powered financial recommendations

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Open a Pull Request

---

## Author

**Nikhil Verma**

- GitHub: https://github.com/nikhil2005verma

---

## Acknowledgements

Special thanks to the teams behind **FastMCP**, **FastAPI**, **Auth0**, and the **Model Context Protocol (MCP)** ecosystem for providing the tools and standards that made this project possible.