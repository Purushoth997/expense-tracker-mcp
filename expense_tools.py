"""Core business logic and handlers for Expense Tracker MCP Server.

Provides formatted tool responses, resource serialization, and prompt generation,
bridging the MCP interface and the SQLite database layer.
"""

from __future__ import annotations

import calendar
import datetime
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from database import (
    add_expense as db_add_expense,
    format_inr,
    get_monthly_expenses as db_get_monthly_expenses,
    get_monthly_total as db_get_monthly_total,
    get_top_categories as db_get_top_categories,
)


def handle_add_expense(
    amount: Any,
    category: Any,
    description: Any,
    expense_date: Optional[str] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> str:
    """Handle adding an expense and return a formatted human- and AI-readable confirmation.

    Catches validation errors and returns helpful error messages.
    """
    try:
        record = db_add_expense(
            amount=amount,
            category=category,
            description=description,
            expense_date=expense_date,
            db_path=db_path,
        )
        return (
            f"Expense recorded successfully!\n"
            f"• ID: {record['id']}\n"
            f"• Amount: {record['amount_inr']}\n"
            f"• Category: {record['category']}\n"
            f"• Description: {record['description']}\n"
            f"• Date: {record['expense_date']}"
        )
    except ValueError as e:
        return f"Error adding expense: {e}"
    except Exception as e:
        return f"Unexpected error while saving expense: {e}"


def handle_monthly_total(
    year: Any,
    month: Any,
    db_path: Optional[Union[str, Path]] = None,
) -> str:
    """Handle monthly total calculation and return a formatted summary in Indian Rupees (INR)."""
    try:
        data = db_get_monthly_total(year=year, month=month, db_path=db_path)
        year_val = data["year"]
        month_name = data["month_name"]
        total_inr = data["total_inr"]
        count = data["transaction_count"]

        if count == 0:
            return (
                f"Monthly Spending Summary for {month_name} {year_val}:\n"
                f"• Total Spending: ₹0.00\n"
                f"• Total Transactions: 0 (No expenses recorded for this month)"
            )

        return (
            f"Monthly Spending Summary for {month_name} {year_val}:\n"
            f"• Total Spending: {total_inr}\n"
            f"• Total Transactions: {count}"
        )
    except ValueError as e:
        return f"Error calculating monthly total: {e}"
    except Exception as e:
        return f"Unexpected error while calculating monthly total: {e}"


def handle_top_categories(
    year: Any,
    month: Any,
    limit: Any = 5,
    db_path: Optional[Union[str, Path]] = None,
) -> str:
    """Handle top categories calculation and return a ranked breakdown with percentages."""
    try:
        data = db_get_top_categories(year=year, month=month, limit=limit, db_path=db_path)
        year_val = data["year"]
        month_name = data["month_name"]
        categories = data["categories"]
        total_inr = data["month_total_inr"]
        total_tx = data["total_transactions"]

        if not categories or total_tx == 0:
            return f"No expenses recorded for {month_name} {year_val}."

        lines = [f"Top Spending Categories for {month_name} {year_val}:"]
        for rank, cat in enumerate(categories, start=1):
            lines.append(
                f"{rank}. {cat['category']}: {cat['total_inr']} "
                f"({cat['percentage_of_total']}% of total, {cat['transaction_count']} transaction{'s' if cat['transaction_count'] != 1 else ''})"
            )

        lines.append(f"\nOverall Month Total: {total_inr} across {total_tx} transaction{'s' if total_tx != 1 else ''}.")
        return "\n".join(lines)
    except ValueError as e:
        return f"Error fetching top categories: {e}"
    except Exception as e:
        return f"Unexpected error while fetching top categories: {e}"


def handle_monthly_resource(
    year: Optional[Any] = None,
    month: Optional[Any] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> str:
    """Handle resource request for monthly expenses, returning structured JSON."""
    data = db_get_monthly_expenses(year=year, month=month, db_path=db_path)
    return json.dumps(data, indent=2, ensure_ascii=False)


def generate_budget_summary_prompt(
    year: Optional[Any] = None,
    month: Optional[Any] = None,
) -> str:
    """Generate the budget_summary prompt guiding the AI to analyze monthly spending."""
    today = datetime.date.today()
    target_year = today.year if year is None else int(year)
    target_month = today.month if month is None else int(month)
    month_name = calendar.month_name[target_month]

    return (
        f"You are an empathetic, insightful, and practical personal finance assistant.\n"
        f"Please review and summarize the user's spending data for {month_name} {target_year}.\n\n"
        f"Instructions:\n"
        f"1. Summarize total spending for {month_name} {target_year} in Indian Rupees (INR).\n"
        f"2. Identify the highest-spending categories, noting their total amounts and proportions of spending.\n"
        f"3. Highlight notable spending patterns, trends, or unusual transactions based solely on recorded data.\n"
        f"4. Provide practical, constructive, and non-judgmental budgeting observations.\n"
        f"5. Never invent expenses, totals, or financial information that do not exist in the database.\n"
        f"6. If no expenses or very few records are available, clearly state that there is insufficient data to draw meaningful conclusions, and guide the user on recording recent expenses."
    )
