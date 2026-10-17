"""Integration tests for MCP Tools, Resource, and Prompt."""

import json
from pathlib import Path
import pytest

from expense_tools import (
    generate_budget_summary_prompt,
    handle_add_expense,
    handle_monthly_resource,
    handle_monthly_total,
    handle_top_categories,
)
from main import mcp


def test_handle_add_expense(temp_db_path: Path):
    """Test handle_add_expense returns structured confirmation text."""
    res = handle_add_expense(
        amount=250.0,
        category="Food",
        description="Lunch",
        expense_date="2026-10-17",
        db_path=temp_db_path,
    )
    assert "Expense recorded successfully!" in res
    assert "• Amount: ₹250.00" in res
    assert "• Category: Food" in res
    assert "• Description: Lunch" in res
    assert "• Date: 2026-10-17" in res


def test_handle_add_expense_validation_error(temp_db_path: Path):
    """Test handle_add_expense safely returns error string on invalid input without crashing."""
    err_amount = handle_add_expense(-50, "Food", "Lunch", db_path=temp_db_path)
    assert "Error adding expense:" in err_amount

    err_cat = handle_add_expense(100, "", "Lunch", db_path=temp_db_path)
    assert "Error adding expense:" in err_cat

    err_date = handle_add_expense(100, "Food", "Lunch", expense_date="2026-99-99", db_path=temp_db_path)
    assert "Error adding expense:" in err_date


def test_handle_monthly_total(temp_db_path: Path):
    """Test handle_monthly_total with expenses present and empty."""
    # Empty
    empty_res = handle_monthly_total(year=2026, month=10, db_path=temp_db_path)
    assert "Monthly Spending Summary for October 2026" in empty_res
    assert "Total Spending: ₹0.00" in empty_res
    assert "Total Transactions: 0" in empty_res

    # Add records
    handle_add_expense(500, "Food", "Dinner", "2026-10-10", db_path=temp_db_path)
    handle_add_expense(250, "Transport", "Taxi", "2026-10-11", db_path=temp_db_path)

    populated_res = handle_monthly_total(year=2026, month=10, db_path=temp_db_path)
    assert "Total Spending: ₹750.00" in populated_res
    assert "Total Transactions: 2" in populated_res


def test_handle_top_categories(temp_db_path: Path):
    """Test handle_top_categories ranks categories and handles empty data."""
    # Empty
    empty_res = handle_top_categories(year=2026, month=10, db_path=temp_db_path)
    assert "No expenses recorded for October 2026." in empty_res

    # Populate
    handle_add_expense(900, "Food", "Groceries", "2026-10-01", db_path=temp_db_path)
    handle_add_expense(100, "Transport", "Bus", "2026-10-02", db_path=temp_db_path)

    res = handle_top_categories(year=2026, month=10, limit=2, db_path=temp_db_path)
    assert "Top Spending Categories for October 2026:" in res
    assert "1. Food: ₹900.00 (90.0% of total, 1 transaction)" in res
    assert "2. Transport: ₹100.00 (10.0% of total, 1 transaction)" in res
    assert "Overall Month Total: ₹1,000.00 across 2 transactions." in res


def test_handle_monthly_resource_json(temp_db_path: Path):
    """Test resource expenses://monthly returns valid structured JSON."""
    handle_add_expense(150, "Education", "Notebook", "2026-10-05", db_path=temp_db_path)

    json_str = handle_monthly_resource(year=2026, month=10, db_path=temp_db_path)
    data = json.loads(json_str)

    assert data["year"] == 2026
    assert data["month"] == 10
    assert data["record_count"] == 1
    assert data["total_amount"] == 150.0
    assert data["total_inr"] == "₹150.00"
    assert len(data["expenses"]) == 1
    assert data["expenses"][0]["category"] == "Education"
    assert data["expenses"][0]["description"] == "Notebook"


def test_generate_budget_summary_prompt():
    """Test budget_summary prompt text generator contains required guidance."""
    prompt_text = generate_budget_summary_prompt(year=2026, month=10)
    assert "October 2026" in prompt_text
    assert "Indian Rupees (INR)" in prompt_text
    assert "highest-spending categories" in prompt_text
    assert "Never invent expenses" in prompt_text
    assert "insufficient data" in prompt_text


@pytest.mark.anyio
async def test_mcp_server_registration_and_calls(monkeypatch, temp_db_path: Path):
    """Test calling tools, resource, and prompt through the FastMCP server instance."""
    # Point server to temporary test DB
    monkeypatch.setenv("EXPENSE_TRACKER_DB_PATH", str(temp_db_path))

    # 1. Verify tools are listed
    tools = await mcp.list_tools()
    tool_names = {t.name for t in tools}
    assert "add_expense" in tool_names
    assert "monthly_total" in tool_names
    assert "top_categories" in tool_names

    # 2. Call add_expense tool
    add_result = await mcp.call_tool(
        "add_expense",
        {"amount": 350.0, "category": "Food", "description": "Team snacks", "expense_date": "2026-10-15"},
    )
    assert "Expense recorded successfully!" in add_result.content[0].text

    # 3. Call monthly_total tool
    total_result = await mcp.call_tool("monthly_total", {"year": 2026, "month": 10})
    assert "Total Spending: ₹350.00" in total_result.content[0].text

    # 4. Call top_categories tool
    top_result = await mcp.call_tool("top_categories", {"year": 2026, "month": 10, "limit": 5})
    assert "Top Spending Categories" in top_result.content[0].text
    assert "Food: ₹350.00" in top_result.content[0].text

    # 5. Verify resource
    resources = await mcp.list_resources()
    assert any(str(r.uri) == "expenses://monthly" for r in resources)

    # 6. Verify prompt
    prompts = await mcp.list_prompts()
    assert any(p.name == "budget_summary" for p in prompts)
    prompt_res = await mcp.get_prompt("budget_summary", {"year": "2026", "month": "10"})
    assert "October 2026" in prompt_res.messages[0].content.text
