# 🎤 5-Minute Internship Mentor Demo Script
## Expense Tracker MCP Server

This script provides a structured, minute-by-minute walkthrough to demonstrate your project to your internship mentor, with clear conceptual explanations of the **Host**, **Client**, **Server**, **Tools**, **Resource**, **Prompt**, and **MCP Inspector**.

---

## 🧠 Part 1: Conceptual Architecture (The 7 Core Concepts)

Before running the live commands, be prepared to explain these 7 fundamental MCP concepts:

| Concept | What It Is | How It Is Implemented in This Project |
|---|---|---|
| **1. Host** | The container or environment that runs the MCP Client. | **Claude Desktop** application or the **Node.js process** running the MCP Inspector. |
| **2. Client** | The MCP layer inside the host that negotiates capabilities, sends JSON-RPC requests, and passes tool outputs to the LLM. | Claude's internal MCP client or the MCP Inspector client engine communicating via JSON-RPC 2.0. |
| **3. Server** | The local background service exposing tools, resources, and prompts. | Our Python application (`main.py`) running on `stdio` transport, backed by SQLite (`database.py`). |
| **4. Tools** | Executable functions with side-effects or computation that the AI can call. | • `add_expense`: inserts records into SQLite with validation.<br>• `monthly_total`: calculates total spend & record count in INR.<br>• `top_categories`: ranks spending categories with percentages. |
| **5. Resource** | Read-only contextual data that the AI or user can read without side-effects. | `expenses://monthly`: returns real-time current month records as structured JSON. |
| **6. Prompt** | A reusable, structured prompt template that steers the AI assistant's reasoning and tone. | `budget_summary`: guides the AI to analyze spending, detect patterns, give non-judgmental advice, and never invent records. |
| **7. MCP Inspector** | A browser-based debugging tool provided by Anthropic / MCP team to test servers in isolation. | Launched via `npx @modelcontextprotocol/inspector .\.venv\Scripts\python.exe main.py`. |

---

## ⏱ Part 2: Minute-by-Minute Live Demo Walkthrough

### 🕒 Minute 0:00 – 1:00 | Introduction & Architectural Overview
**What to Say:**
> *"Good morning/afternoon! Today I am presenting my internship project: an Expense Tracker MCP Server built using Python, the Model Context Protocol SDK, and SQLite.*
>
> *In the MCP architecture, the **Host** is the application like Claude Desktop, the **Client** communicates over JSON-RPC 2.0, and our **Server** runs locally in Python. It exposes three **Tools** for adding expenses and calculating totals, one read-only **Resource** (`expenses://monthly`) for monthly expense data, and one reusable **Prompt** (`budget_summary`) that guides the AI's financial advice.*
>
> *All data is saved persistently in a local SQLite database with parameterized SQL queries to guarantee zero SQL injection."*

**What to Show on Screen:**
Open the project folder and show the clean architecture:
- `database.py` (Database layer & input validation)
- `expense_tools.py` (Business logic & INR formatting)
- `main.py` (MCP Server with tools, resource, and prompt)

---

### 🕒 Minute 1:00 – 2:00 | Automated Tests & Reliability (15 Tests)
**What to Say:**
> *"Before testing with an AI client, I wrote a comprehensive automated test suite with 15 pytest tests. These tests use an isolated temporary database fixture, ensuring tests never touch real records.*
>
> *We verify: record insertion, monthly aggregations across different months, category percentage calculations, input validation (rejecting negative amounts, empty categories, and invalid dates like February 31st), and empty database behavior."*

**Command to Run in PowerShell:**
```powershell
$env:PYTHONUTF8=1; .\.venv\Scripts\pytest.exe -v
```

**Expected Result:**
All 15 tests pass green in under 2 seconds:
```
tests/test_database.py::test_add_expense_success PASSED
tests/test_database.py::test_add_expense_default_date PASSED
tests/test_database.py::test_monthly_total_calculation PASSED
tests/test_database.py::test_category_ranking PASSED
tests/test_database.py::test_invalid_expense_amounts_and_dates PASSED
tests/test_database.py::test_empty_database_behavior PASSED
...
============================= 15 passed in 1.41s ==============================
```

---

### 🕒 Minute 2:00 – 3:00 | End-to-End JSON-RPC Protocol Verification
**What to Say:**
> *"Now let's verify that our server speaks the standard Model Context Protocol over stdio JSON-RPC. I created a protocol verification script that acts as an MCP client.*
>
> *It sends `initialize`, performs capability negotiation, discovers tools, calls `add_expense`, `monthly_total`, and `top_categories`, reads the `expenses://monthly` resource, and fetches the `budget_summary` prompt."*

**Command to Run in PowerShell:**
```powershell
.\.venv\Scripts\python.exe verify_mcp_protocol.py
```

**Expected Result:**
Shows step-by-step confirmation of all 7 protocol steps:
```
1. Testing 'initialize'...
   ✅ Server Initialized!
2. Testing 'tools/list'...
   ✅ Discovered tools: ['add_expense', 'monthly_total', 'top_categories']
3. Testing 'tools/call' -> add_expense...
   ✅ Expense recorded successfully! (Amount: ₹250.00 | Category: Food)
4. Testing 'tools/call' -> monthly_total...
   ✅ Total Spending: ₹1,000.00 (2 transactions)
5. Testing 'tools/call' -> top_categories...
   ✅ Top Spending Categories: Transport 75%, Food 25%
6. Testing 'resources/list' and 'resources/read'...
   ✅ Resource parsed successfully! (record_count: 2)
7. Testing 'prompts/list' and 'prompts/get'...
   ✅ Prompt retrieved: budget_summary
```

---

### 🕒 Minute 3:00 – 4:00 | Natural Language AI Interaction
**What to Say:**
> *"Now let's see how an AI assistant answers natural language questions using our MCP tools. We have a simulation script demonstrating the three required user questions."*

**Command to Run in PowerShell:**
```powershell
.\.venv\Scripts\python.exe demo_queries.py
```

**What to Point Out:**
1. **Scenario 1**: User asks: *"Record ₹250 for lunch under Food."*
   - AI calls `add_expense` with `amount: 250.0, category: 'Food', description: 'lunch'`.
   - Result: Formatted confirmation in Indian Rupees with ID.
2. **Scenario 2**: User asks: *"What is my total spending this month?"*
   - AI calls `monthly_total` with current year and month.
   - Result: Exact sum calculated directly by the database (e.g., `₹5,040.00 across 8 transactions`).
3. **Scenario 3**: User asks: *"Which category has the highest spending this month?"*
   - AI calls `top_categories`.
   - Result: Categorized breakdown with exact percentages (e.g., Education: 47.6%, Food: 26.6%).

---

### 🕒 Minute 4:00 – 4:45 | Testing in MCP Inspector UI
**What to Say:**
> *"To allow developers and mentors to inspect the server in a live web UI, we can launch the official MCP Inspector."*

**Command to Run in PowerShell:**
```powershell
npx @modelcontextprotocol/inspector .\.venv\Scripts\python.exe main.py
```

**What to Show in the Browser:**
1. Open the URL provided by the inspector (e.g. `http://localhost:5173` or `http://localhost:6274`).
2. Show the **Tools** tab:
   - Click `add_expense`, show the JSON schema generated from Python type hints, and click **Run Tool**.
3. Show the **Resources** tab:
   - Click `expenses://monthly` and show the structured JSON data.
4. Show the **Prompts** tab:
   - Click `budget_summary` and show the prompt template.

---

### 🕒 Minute 4:45 – 5:00 | Conclusion & Q&A
**What to Say:**
> *"To conclude, this project satisfies all project criteria:
> 1. Persistent, parameterized SQLite storage.
> 2. 3 Tools, 1 Resource, and 1 Prompt with strict input validation.
> 3. Native Indian Rupee formatting.
> 4. 15 passing automated tests.
> 5. Ready for Claude Desktop and GitHub.
>
> Thank you, and I am happy to answer any questions!"*

---

## 💡 Potential Mentor Questions & How to Answer

**Q1: How do you prevent SQL injection?**  
> *"All SQL statements in `database.py` use parameterized queries with `?` placeholders. User inputs are never concatenated directly into SQL strings. In addition, we validate data types and ranges before the query is executed."*

**Q2: What happens if an expense is added with a negative amount or an invalid date?**  
> *"Our `validate_expense_input` function catches non-positive amounts, empty strings, and malformed dates like '2026-02-31' using regex and `datetime.date.fromisoformat`. Rather than crashing, the tool returns a clear, user-friendly error message so the AI can explain the mistake to the user."*

**Q3: Why did you use `expenses://monthly` as a resource instead of a tool?**  
> *"In MCP, **resources** represent read-only context that can be attached to the AI context like a file or live feed without performing side-effects. **Tools** are intended for operations that perform calculations or mutate data (like adding an expense)."*

**Q4: How do you handle Windows UTF-8 console issues with the Rupee symbol (`₹`)?**  
> *"Windows consoles default to CP-1252, which can cause `UnicodeEncodeError`. We explicitly reconfigure `sys.stdout` and `sys.stderr` to UTF-8 in `main.py` and set `ensure_ascii=False` during JSON serialization, ensuring seamless cross-platform support."*
