"""Demonstration of AI natural language queries mapping to Expense Tracker MCP tools.

Shows how an AI client (Claude Desktop, etc.) processes user prompts, calls the
corresponding MCP tools, resources, and prompts, and returns clear responses.
"""

from __future__ import annotations

import asyncio
import datetime
import os
from pathlib import Path
import sys

# Configure UTF-8 encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from database import format_inr
from main import mcp


async def run_demo():
    print("=" * 70)
    print("🤖 EXPENSE TRACKER MCP SERVER - AI INTERACTION DEMONSTRATION")
    print("=" * 70)

    now = datetime.date.today()
    curr_year = now.year
    curr_month = now.month

    # -------------------------------------------------------------
    # Scenario 1: Natural Language Expense Recording
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("📌 SCENARIO 1: Natural Language Expense Addition")
    print("User: 'Record ₹250 for lunch under Food.'")
    print("AI Decision:")
    print("  • Tool Selected : add_expense")
    print("  • Arguments     : {'amount': 250.0, 'category': 'Food', 'description': 'lunch'}")
    print("-" * 70)

    result_1 = await mcp.call_tool(
        "add_expense",
        {"amount": 250.0, "category": "Food", "description": "lunch"},
    )
    print("MCP Server Output:\n" + result_1.content[0].text)

    # Add a couple more expenses to make queries interesting
    await mcp.call_tool(
        "add_expense",
        {"amount": 650.0, "category": "Transport", "description": "Weekly metro card recharge"},
    )
    await mcp.call_tool(
        "add_expense",
        {"amount": 420.0, "category": "Food", "description": "Grocery shopping"},
    )
    await mcp.call_tool(
        "add_expense",
        {"amount": 1200.0, "category": "Education", "description": "Python & Cloud textbook"},
    )

    # -------------------------------------------------------------
    # Scenario 2: Natural Language Monthly Total Query
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("📌 SCENARIO 2: Natural Language Monthly Spending Query")
    print("User: 'What is my total spending this month?'")
    print("AI Decision:")
    print("  • Tool Selected : monthly_total")
    print(f"  • Arguments     : {{'year': {curr_year}, 'month': {curr_month}}}")
    print("-" * 70)

    result_2 = await mcp.call_tool(
        "monthly_total",
        {"year": curr_year, "month": curr_month},
    )
    print("MCP Server Output:\n" + result_2.content[0].text)

    # -------------------------------------------------------------
    # Scenario 3: Natural Language Top Spending Categories Query
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("📌 SCENARIO 3: Natural Language Top Spending Categories Query")
    print("User: 'Which category has the highest spending this month?'")
    print("AI Decision:")
    print("  • Tool Selected : top_categories")
    print(f"  • Arguments     : {{'year': {curr_year}, 'month': {curr_month}, 'limit': 3}}")
    print("-" * 70)

    result_3 = await mcp.call_tool(
        "top_categories",
        {"year": curr_year, "month": curr_month, "limit": 3},
    )
    print("MCP Server Output:\n" + result_3.content[0].text)

    # -------------------------------------------------------------
    # Scenario 4: Reading the Monthly Expenses Resource
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("📌 SCENARIO 4: AI Reads MCP Resource 'expenses://monthly'")
    print("Resource URI: expenses://monthly")
    print("-" * 70)

    resource_content = await mcp.read_resource("expenses://monthly")
    raw_text = resource_content[0].content if hasattr(resource_content[0], "content") else str(resource_content[0])
    # Display first few lines
    lines = raw_text.splitlines()[:15]
    print("\n".join(lines) + "\n... (truncated for preview)")

    # -------------------------------------------------------------
    # Scenario 5: Using the Budget Summary Prompt
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("📌 SCENARIO 5: AI Activates Prompt 'budget_summary'")
    print("Prompt Name: budget_summary")
    print("-" * 70)

    prompt_res = await mcp.get_prompt("budget_summary", {"year": str(curr_year), "month": str(curr_month)})
    prompt_msg = prompt_res.messages[0].content.text
    print("Prompt Instructions for AI:\n" + prompt_msg)

    print("\n" + "=" * 70)
    print("✨ Demo completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_demo())
