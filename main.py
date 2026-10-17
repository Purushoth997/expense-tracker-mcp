"""Expense Tracker MCP Server.

An MCP server that allows AI assistants (such as Claude Desktop) to manage expenses,
track budgets, and analyze spending patterns using persistent SQLite storage.
"""

from __future__ import annotations

import sys
from typing import Optional

# Ensure standard streams use UTF-8 encoding on Windows to prevent UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Import FastMCP / MCPServer supporting both MCP v1.x and v2.x
try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

from database import init_db
from expense_tools import (
    generate_budget_summary_prompt,
    handle_add_expense,
    handle_monthly_resource,
    handle_monthly_total,
    handle_top_categories,
)

# Automatically initialize database when the server module is loaded
init_db()

# Initialize the MCP Server
mcp = FastMCP(
    "expense-tracker",
    instructions="Personal Expense Tracker MCP Server for recording expenses and analyzing spending.",
)


@mcp.tool(
    description=(
        "Add a new expense to the database. "
        "Inputs: amount (positive number in INR), category (e.g., Food, Transport, Education, Shopping, Entertainment), "
        "description (short text), and optional expense_date (YYYY-MM-DD, defaults to today). "
        "Returns clear confirmation with expense ID and saved details."
    )
)
def add_expense(
    amount: float,
    category: str,
    description: str,
    expense_date: Optional[str] = None,
) -> str:
    """Record a new expense."""
    return handle_add_expense(
        amount=amount,
        category=category,
        description=description,
        expense_date=expense_date,
    )


@mcp.tool(
    description=(
        "Calculate total spending and transaction count for a specified month and year. "
        "Inputs: year (e.g. 2026), month (1 to 12). "
        "Returns the total formatted in Indian Rupees (INR) and the number of records."
    )
)
def monthly_total(
    year: int,
    month: int,
) -> str:
    """Calculate total expenses for a specified month."""
    return handle_monthly_total(
        year=year,
        month=month,
    )


@mcp.tool(
    description=(
        "Identify expense categories with the highest spending for a specified month. "
        "Inputs: year (e.g. 2026), month (1 to 12), and optional limit (default: 5). "
        "Returns categories ranked by total spending in descending order with transaction counts and percentages."
    )
)
def top_categories(
    year: int,
    month: int,
    limit: int = 5,
) -> str:
    """Get top spending categories for a specified month."""
    return handle_top_categories(
        year=year,
        month=month,
        limit=limit,
    )


@mcp.resource(
    "expenses://monthly",
    mime_type="application/json",
    description="Read-only structured JSON records of all expenses recorded in the current month.",
)
def get_monthly_expenses() -> str:
    """Expose expense records for the current month as structured JSON."""
    return handle_monthly_resource()


@mcp.prompt(
    "budget_summary",
    description="Structured prompt to guide the AI assistant in analyzing monthly spending habits and budget advice.",
)
def budget_summary_prompt(
    year: str = "",
    month: str = "",
) -> str:
    """Generate budget summary prompt for an AI assistant."""
    y = int(year) if year and year.strip() else None
    m = int(month) if month and month.strip() else None
    return generate_budget_summary_prompt(year=y, month=m)


def main() -> None:
    """Server entry point."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
