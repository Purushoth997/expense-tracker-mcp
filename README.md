# 💰 Personal Expense Tracker MCP Server

An enterprise-ready, beginner-friendly **Model Context Protocol (MCP)** server built in Python that enables AI assistants (such as Claude Desktop, Cursor, and any MCP-compatible client) to manage personal expenses, monitor budgets, and analyze spending habits using persistent local SQLite storage.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Project Architecture](#-project-architecture)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [MCP Interface Specification](#-mcp-interface-specification)
  - [Tools](#1-mcp-tools)
  - [Resource](#2-mcp-resource)
  - [Prompt](#3-mcp-prompt)
- [Running the Server](#-running-the-server)
- [Testing with MCP Inspector](#-testing-with-mcp-inspector)
- [Connecting to AI Applications](#-connecting-to-ai-applications)
  - [Claude Desktop Configuration](#claude-desktop-configuration)
- [Natural Language Usage Examples](#-natural-language-usage-examples)
- [Automated Testing](#-automated-testing)
- [5-Minute Mentor Demo Script](#-5-minute-mentor-demo-script)
- [Troubleshooting & FAQ](#-troubleshooting--faq)
- [Security & Safe Practices](#-security--safe-practices)
- [Git & GitHub Setup](#-git--github-setup)

---

## 🌟 Overview

The **Expense Tracker MCP Server** bridges standard AI chat assistants with local, structured financial accounting. Instead of relying on manual spreadsheet entries or sending sensitive financial data to cloud third parties, the assistant communicates directly with a local SQLite database via standard MCP protocols.

All monetary amounts are validated, stored with timestamps, and presented in **Indian Rupee (INR - ₹)** formatting following Indian numbering standards (e.g., `₹1,250.00`, `₹1,00,000.00`).

---

## ✨ Key Features

- **Strict Input Validation**: Prevents zero, negative, invalid, or non-numeric amounts, missing descriptions/categories, and invalid calendar dates.
- **SQL Injection Prevention**: Built entirely with parameterized SQL queries (`?`) and strict type checks.
- **Persistent Local SQLite Storage**: Database and schema are automatically initialized on server startup.
- **Currency Localization**: Native Indian Rupee (`₹`) formatting with proper decimal precision and comma groupings.
- **Complete MCP Primitives**:
  - **3 Tools**: `add_expense`, `monthly_total`, `top_categories`
  - **1 Resource**: `expenses://monthly` (real-time read-only JSON stream)
  - **1 Prompt**: `budget_summary` (finance assistant instructions)
- **100% Test Coverage**: Comprehensive `pytest` test suite covering business logic, edge cases, error conditions, and async MCP server invocations.
- **Platform Agnostic & Windows Resilient**: Explicit UTF-8 stream handling preventing `UnicodeEncodeError` across Windows consoles and standard input/output pipes.

---

## 🛠 Technology Stack

- **Language**: Python 3.10+ (tested on Python 3.14)
- **Protocol SDK**: Official Model Context Protocol Python SDK (`mcp>=1.2.0`)
- **Database**: SQLite 3 (Python built-in `sqlite3`)
- **Testing Framework**: `pytest>=8.0.0`, `anyio`
- **Testing Tools**: `@modelcontextprotocol/inspector`
- **Version Control**: Git & GitHub

---

## 📂 Project Architecture

```
expense-tracker/
├── database.py             # SQLite database layer, schema, CRUD & queries
├── expense_tools.py        # Business logic, formatting, and prompt generator
├── main.py                 # FastMCP / MCPServer definition and entry point
├── verify_mcp_protocol.py  # End-to-end JSON-RPC stdio protocol test script
├── demo_queries.py         # AI natural language simulation script
├── pytest.ini              # Pytest configuration (pythonpath discovery)
├── requirements.txt        # Production & testing dependencies
├── .gitignore              # Ignores venvs, local SQLite DBs, and cache files
├── README.md               # Comprehensive documentation and mentor guide
└── tests/
    ├── conftest.py         # Isolated temporary database fixture
    ├── test_database.py    # Database unit tests & input validation tests
    └── test_server.py      # MCP tool, resource, prompt & server tests
```

---

## ⚙️ Prerequisites

1. **Python 3.10 or higher**
   ```powershell
   python --version
   ```
2. **Git**
   ```powershell
   git --version
   ```
3. **Node.js & npm** (optional, recommended for MCP Inspector)
   ```powershell
   node --version
   npx --version
   ```

---

## 🚀 Installation & Setup

### 1. Clone or Open the Workspace

```powershell
cd "c:\Users\purus\OneDrive\Desktop\expense tracker"
```

### 2. Create and Activate a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## 🔌 MCP Interface Specification

### 1. MCP Tools

| Tool Name | Parameters | Description |
|---|---|---|
| `add_expense` | `amount` (float > 0)<br>`category` (str)<br>`description` (str)<br>`expense_date` (optional YYYY-MM-DD) | Records a new expense record in SQLite with validation and returns formatted confirmation. |
| `monthly_total` | `year` (int, 1900–2100)<br>`month` (int, 1–12) | Computes total spending in INR and transaction count for the requested month. Returns ₹0.00 if no entries exist. |
| `top_categories` | `year` (int)<br>`month` (int, 1–12)<br>`limit` (optional int > 0, default: 5) | Groups expenses by category, ranks them in descending order by spend, and calculates percentage shares. |

### 2. MCP Resource

- **URI**: `expenses://monthly`
- **MIME Type**: `application/json`
- **Description**: Exposes all expense records for the current calendar month in structured, read-only JSON format.
- **Sample Payload**:
  ```json
  {
    "year": 2026,
    "month": 10,
    "month_name": "October",
    "record_count": 2,
    "total_amount": 1000.0,
    "total_inr": "₹1,000.00",
    "expenses": [
      {
        "id": 1,
        "amount": 250.0,
        "amount_inr": "₹250.00",
        "category": "Food",
        "description": "Lunch at cafeteria",
        "expense_date": "2026-10-17",
        "created_at": "2026-10-17 12:30:00"
      }
    ]
  }
  ```

### 3. MCP Prompt

- **Prompt Name**: `budget_summary`
- **Arguments**:
  - `year` (optional string): Target year
  - `month` (optional string): Target month (1–12)
- **Role**: Guides the AI assistant to provide an empathetic, grounded budget analysis:
  - Summarize total monthly spending in INR.
  - Detail highest-spending categories and their percentages.
  - Surface spending patterns strictly based on recorded data.
  - Provide non-judgmental, practical savings recommendations.
  - Explicitly acknowledge when insufficient data is available.

---

## 🖥 Running the Server

To launch the server locally over standard input/output (stdio):

```powershell
.\.venv\Scripts\python.exe main.py
```

*Note: The server runs as a background JSON-RPC stdio process awaiting commands from an MCP client.*

---

## 🔍 Testing with MCP Inspector

The official MCP Inspector provides an interactive web-based UI to inspect and test all tools, resources, and prompts.

Run the inspector with your virtual environment Python:

```powershell
npx @modelcontextprotocol/inspector .\.venv\Scripts\python.exe main.py
```

### In the Inspector Web UI:
1. Navigate to the **Tools** tab:
   - Select `add_expense` and input `{"amount": 350.0, "category": "Food", "description": "Lunch"}` -> Click **Run Tool**.
   - Select `monthly_total` and input `{"year": 2026, "month": 10}` -> Click **Run Tool**.
   - Select `top_categories` and input `{"year": 2026, "month": 10, "limit": 3}` -> Click **Run Tool**.
2. Navigate to the **Resources** tab:
   - Click `expenses://monthly` to inspect the live JSON payload.
3. Navigate to the **Prompts** tab:
   - Select `budget_summary` and view the generated instructions.

---

## 🤖 Connecting to AI Applications

### Claude Desktop Configuration

Claude Desktop connects to local MCP servers through its configuration file.

1. Open or create the Claude Desktop config file:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
     *(Full path: `C:\Users\<YourUsername>\AppData\Roaming\Claude\claude_desktop_config.json`)*
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Add the `expense-tracker` server entry:

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "C:\\Users\\purus\\OneDrive\\Desktop\\expense tracker\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\purus\\OneDrive\\Desktop\\expense tracker\\main.py"
      ],
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

3. Restart Claude Desktop. You will see a 🔨 (hammer) icon in Claude indicating that the 3 expense tracker tools are active and ready!

---

## 💬 Natural Language Usage Examples

When integrated with an AI assistant, you can ask queries in natural English:

### Question 1: Adding an expense
> **User**: *"Record ₹250 for lunch under Food."*  
> **AI Action**: Calls `add_expense(amount=250.0, category="Food", description="lunch")`  
> **Assistant Response**:
> ```
> Expense recorded successfully!
> • ID: 1
> • Amount: ₹250.00
> • Category: Food
> • Description: lunch
> • Date: 2026-10-17
> ```

### Question 2: Inquiring about total monthly spend
> **User**: *"What is my total spending this month?"*  
> **AI Action**: Calls `monthly_total(year=2026, month=10)`  
> **Assistant Response**:
> ```
> Monthly Spending Summary for October 2026:
> • Total Spending: ₹2,520.00
> • Total Transactions: 4
> ```

### Question 3: Finding top spending categories
> **User**: *"Which category has the highest spending this month?"*  
> **AI Action**: Calls `top_categories(year=2026, month=10, limit=3)`  
> **Assistant Response**:
> ```
> Top Spending Categories for October 2026:
> 1. Education: ₹1,200.00 (47.6% of total, 1 transaction)
> 2. Food: ₹670.00 (26.6% of total, 2 transactions)
> 3. Transport: ₹650.00 (25.8% of total, 1 transaction)
> 
> Overall Month Total: ₹2,520.00 across 4 transactions.
> ```

---

## 🧪 Automated Testing

The project includes 15 automated pytest tests verifying database initialization, CRUD operations, constraints, ranking calculations, error handling, and MCP protocol integration.

### Run All Tests:
```powershell
$env:PYTHONUTF8=1
.\.venv\Scripts\pytest.exe -v
```

### Run End-to-End MCP Protocol Verification:
```powershell
.\.venv\Scripts\python.exe verify_mcp_protocol.py
```

### Run Natural Language Query Simulation:
```powershell
.\.venv\Scripts\python.exe demo_queries.py
```

---

## ⏱ 5-Minute Mentor Demo Script

Use this exact walkthrough when presenting the project to your mentor:

| Time | Step | Action & Narration | Command / Action |
|---|---|---|---|
| **0:00 - 0:45** | **Architecture & Concept** | Introduce the project: "This is an MCP server written in Python using SQLite. It implements the Model Context Protocol standard with 3 tools, 1 resource, and 1 prompt, allowing AI assistants to track personal finances." | Show project structure (`database.py`, `expense_tools.py`, `main.py`). |
| **0:45 - 1:45** | **Automated Tests** | "First, let's verify reliability. We wrote 15 pytest tests verifying input validation, edge cases, category percentages, and currency formatting." | Run: `.\.venv\Scripts\pytest.exe -v` *(All 15 tests pass green)*. |
| **1:45 - 2:45** | **MCP Protocol Verification** | "Here we run a real stdio JSON-RPC client verifying server handshake, tool discovery, tool execution, resource reading, and prompt generation." | Run: `.\.venv\Scripts\python.exe verify_mcp_protocol.py`. |
| **2:45 - 3:45** | **Natural Language Simulation** | "Now let's demonstrate the 3 required natural language user scenarios: adding ₹250 for lunch, checking monthly total, and identifying top categories." | Run: `.\.venv\Scripts\python.exe demo_queries.py`. |
| **3:45 - 4:30** | **MCP Inspector UI** | "Next, we launch the official MCP Inspector to interactively inspect our tools and live JSON resource in a browser." | Run: `npx @modelcontextprotocol/inspector .\.venv\Scripts\python.exe main.py`. |
| **4:30 - 5:00** | **Q&A & Claude Desktop Setup** | Show the Claude Desktop configuration in `README.md` and explain the security guarantees (parameterized queries, isolated local SQLite DB). | Conclude demo. |

---

## ❓ Troubleshooting & FAQ

#### 1. `UnicodeEncodeError: 'charmap' codec can't encode character '\u20b9'`
- **Cause**: Default Windows PowerShell console code page is legacy CP-1252.
- **Solution**: The code automatically configures `sys.stdout.reconfigure(encoding="utf-8")`. For PowerShell commands, set `$env:PYTHONUTF8=1`.

#### 2. `ModuleNotFoundError: No module named 'mcp'`
- **Cause**: Python is running outside the virtual environment.
- **Solution**: Always use the virtual environment executable: `.\.venv\Scripts\python.exe` or activate `.venv`.

#### 3. Database locking or permission errors
- **Cause**: Multiple write transactions without closing connections.
- **Solution**: All database operations in `database.py` use Python context managers (`with conn:`) ensuring atomic commits and immediate connection closure.

---

## 🔒 Security & Safe Practices

- **Zero SQL Injections**: Queries strictly use parameterized bindings (`?`).
- **No Arbitrary Code Execution**: Inputs are validated against strong type constraints and sanitized.
- **Data Privacy**: All expenses remain in a local, private SQLite database on the user's machine; no financial records are transmitted to cloud telemetry or third parties.
- **Git Exclusions**: `.gitignore` excludes `*.db`, `.env`, and virtual environment directories.

---

## 📦 Git & GitHub Setup

To push this repository to GitHub:

```powershell
# 1. Initialize git (if not already done)
git init

# 2. Stage all project files
git add .

# 3. Create initial commit
git commit -m "feat: complete Expense Tracker MCP Server with tools, resource, prompt and tests"

# 4. Link your remote GitHub repository
# Replace with your actual GitHub repository URL
git remote add origin https://github.com/<your-username>/expense-tracker-mcp.git

# 5. Push to GitHub
git branch -M main
git push -u origin main
```

---

## 🎓 Internship Mentor Evaluation Summary

| Requirement | Implementation Status | Verified By |
|---|---|---|
| **Python 3.10+ & MCP SDK** | ✅ `mcp>=1.2.0` (FastMCP / MCPServer) | `main.py`, `requirements.txt` |
| **Persistent SQLite Storage** | ✅ `expenses` table with auto-initialization | `database.py` |
| **Tool 1: `add_expense`** | ✅ Validates amounts, dates, categories; returns ID & details | `tests/test_database.py`, `verify_mcp_protocol.py` |
| **Tool 2: `monthly_total`** | ✅ Aggregates sum & count; formats INR; handles zero expenses | `tests/test_server.py`, `demo_queries.py` |
| **Tool 3: `top_categories`** | ✅ Ranks spend descending; calculates percentage shares | `tests/test_database.py`, `demo_queries.py` |
| **Resource: `expenses://monthly`** | ✅ Read-only structured JSON with current month expenses | `verify_mcp_protocol.py` |
| **Prompt: `budget_summary`** | ✅ Reusable analysis instructions for AI budgeting advice | `verify_mcp_protocol.py` |
| **Automated Tests** | ✅ 15 passing pytest tests (with temporary DB fixture) | `pytest` |
| **MCP Inspector Ready** | ✅ Tested with `npx @modelcontextprotocol/inspector` | Verified via CLI |
| **AI Integration Guide** | ✅ Complete Claude Desktop config and 3 user scenarios | `README.md`, `demo_queries.py` |
