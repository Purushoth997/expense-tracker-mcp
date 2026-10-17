"""Database management and queries for Expense Tracker MCP Server.

Provides SQLite persistent storage, schema initialization, input validation,
safe parameterized SQL queries, and Indian Rupee (INR) formatting.
"""

from __future__ import annotations

import calendar
import datetime
import math
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union

DEFAULT_DB_FILE = "expenses.db"


def get_db_path(custom_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolve the SQLite database path.

    Order of precedence:
    1. Explicit custom_path argument.
    2. EXPENSE_TRACKER_DB_PATH environment variable.
    3. Default 'expenses.db' in the project directory.
    """
    if custom_path is not None:
        return Path(custom_path)
    env_path = os.getenv("EXPENSE_TRACKER_DB_PATH")
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parent / DEFAULT_DB_FILE


def format_inr(amount: Union[int, float]) -> str:
    """Format a numerical amount into Indian Rupee currency format (e.g., ₹1,250.00, ₹1,00,000.00).

    Uses the Indian numbering grouping (hundreds, then groupings of two for thousands, lakhs, crores).
    """
    try:
        val = float(amount)
        if math.isnan(val) or math.isinf(val):
            return f"₹{amount}"

        is_negative = val < 0
        val = abs(val)
        parts = f"{val:.2f}".split(".")
        int_part = parts[0]
        dec_part = parts[1]

        if len(int_part) <= 3:
            formatted_int = int_part
        else:
            last_three = int_part[-3:]
            rest = int_part[:-3]
            groups = []
            while len(rest) > 2:
                groups.append(rest[-2:])
                rest = rest[:-2]
            if rest:
                groups.append(rest)
            groups.reverse()
            formatted_int = ",".join(groups) + "," + last_three

        prefix = "-₹" if is_negative else "₹"
        return f"{prefix}{formatted_int}.{dec_part}"
    except (ValueError, TypeError):
        return f"₹{amount}"


def get_connection(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """Return a configured SQLite connection with foreign keys and row factory enabled."""
    resolved_path = get_db_path(db_path)
    # Ensure parent directory exists
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(resolved_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[Union[str, Path]] = None) -> None:
    """Initialize the SQLite database with the expenses table and indexes if they do not exist."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL CHECK(amount > 0),
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    expense_date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);"
            )
    finally:
        conn.close()


def validate_expense_input(
    amount: Any,
    category: Any,
    description: Any,
    expense_date: Optional[str] = None,
) -> Tuple[float, str, str, str]:
    """Validate and normalize inputs for adding an expense.

    Raises:
        ValueError: If any input fails validation.
    """
    # 1. Amount validation
    if amount is None:
        raise ValueError("Amount is required and cannot be empty.")
    try:
        amount_val = float(amount)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid amount '{amount}'. Amount must be a valid positive number.")

    if math.isnan(amount_val) or math.isinf(amount_val):
        raise ValueError("Amount must be a finite number.")

    if amount_val <= 0:
        raise ValueError(
            f"Invalid amount {amount_val}. Amount must be a positive number greater than 0."
        )

    # 2. Category validation
    if not isinstance(category, str) or not category.strip():
        raise ValueError("Category is required and cannot be empty.")
    category_val = category.strip()

    # 3. Description validation
    if not isinstance(description, str) or not description.strip():
        raise ValueError("Description is required and cannot be empty.")
    description_val = description.strip()

    # 4. Expense date validation
    if expense_date is None or (isinstance(expense_date, str) and not expense_date.strip()):
        expense_date_val = datetime.date.today().isoformat()
    elif isinstance(expense_date, str):
        cleaned_date = expense_date.strip()
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", cleaned_date):
            raise ValueError(
                f"Invalid date format '{expense_date}'. Expected format is YYYY-MM-DD (e.g., 2026-10-17)."
            )
        try:
            parsed_date = datetime.date.fromisoformat(cleaned_date)
            expense_date_val = parsed_date.isoformat()
        except ValueError:
            raise ValueError(
                f"Invalid calendar date '{expense_date}'. Please provide a valid calendar date in YYYY-MM-DD format."
            )
    else:
        raise ValueError("Expense date must be a string in YYYY-MM-DD format.")

    return round(amount_val, 2), category_val, description_val, expense_date_val


def validate_month_year(year: Any, month: Any) -> Tuple[int, int]:
    """Validate year and month inputs.

    Raises:
        ValueError: If year or month is invalid.
    """
    try:
        year_int = int(year)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid year '{year}'. Year must be a valid 4-digit integer.")

    if year_int < 1900 or year_int > 2100:
        raise ValueError(f"Year {year_int} is out of range. Must be between 1900 and 2100.")

    try:
        month_int = int(month)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid month '{month}'. Month must be an integer between 1 and 12.")

    if month_int < 1 or month_int > 12:
        raise ValueError(f"Month {month_int} is out of range. Month must be an integer between 1 and 12.")

    return year_int, month_int


def add_expense(
    amount: Any,
    category: Any,
    description: Any,
    expense_date: Optional[str] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Validate and insert a new expense record into the SQLite database.

    Returns:
        Dict with recorded expense details including ID and formatted INR amount.
    """
    validated_amount, validated_category, validated_desc, validated_date = (
        validate_expense_input(amount, category, description, expense_date)
    )

    init_db(db_path)
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO expenses (amount, category, description, expense_date)
                VALUES (?, ?, ?, ?);
                """,
                (validated_amount, validated_category, validated_desc, validated_date),
            )
            expense_id = cursor.lastrowid

            # Retrieve created timestamp
            row = conn.execute(
                "SELECT created_at FROM expenses WHERE id = ?;", (expense_id,)
            ).fetchone()
            created_at = row["created_at"] if row else ""

        return {
            "id": expense_id,
            "amount": validated_amount,
            "amount_inr": format_inr(validated_amount),
            "category": validated_category,
            "description": validated_desc,
            "expense_date": validated_date,
            "created_at": created_at,
        }
    finally:
        conn.close()


def get_monthly_total(
    year: Any,
    month: Any,
    db_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Calculate total expenses and count for a specified month.

    Returns:
        Dict with year, month, month name, total amount, formatted INR, and transaction count.
    """
    valid_year, valid_month = validate_month_year(year, month)
    month_prefix = f"{valid_year:04d}-{valid_month:02d}"
    month_name = calendar.month_name[valid_month]

    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0.0) AS total, COUNT(*) AS count
            FROM expenses
            WHERE substr(expense_date, 1, 7) = ?;
            """,
            (month_prefix,),
        )
        row = cursor.fetchone()
        total_amount = float(row["total"]) if row else 0.0
        transaction_count = int(row["count"]) if row else 0

        return {
            "year": valid_year,
            "month": valid_month,
            "month_name": month_name,
            "total_amount": round(total_amount, 2),
            "total_inr": format_inr(total_amount),
            "transaction_count": transaction_count,
        }
    finally:
        conn.close()


def get_top_categories(
    year: Any,
    month: Any,
    limit: Any = 5,
    db_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Identify expense categories with the highest spending for a specified month.

    Returns:
        Dict with year, month, month name, total spending, and ranked category list.
    """
    valid_year, valid_month = validate_month_year(year, month)
    month_prefix = f"{valid_year:04d}-{valid_month:02d}"
    month_name = calendar.month_name[valid_month]

    # Validate limit
    if limit is None:
        limit_int = 5
    else:
        try:
            limit_int = int(limit)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid limit '{limit}'. Limit must be a positive integer.")
        if limit_int <= 0:
            raise ValueError(
                f"Invalid limit {limit_int}. Limit must be a positive integer greater than 0."
            )

    init_db(db_path)
    conn = get_connection(db_path)
    try:
        # First get monthly total for percentage computation
        monthly_total_data = get_monthly_total(valid_year, valid_month, db_path=db_path)
        month_total = monthly_total_data["total_amount"]
        total_transactions = monthly_total_data["transaction_count"]

        cursor = conn.execute(
            """
            SELECT category, COALESCE(SUM(amount), 0.0) AS cat_total, COUNT(*) AS cat_count
            FROM expenses
            WHERE substr(expense_date, 1, 7) = ?
            GROUP BY category
            ORDER BY cat_total DESC, category ASC
            LIMIT ?;
            """,
            (month_prefix, limit_int),
        )
        rows = cursor.fetchall()

        categories: List[Dict[str, Any]] = []
        for row in rows:
            cat_total = float(row["cat_total"])
            cat_count = int(row["cat_count"])
            pct = round((cat_total / month_total * 100), 1) if month_total > 0 else 0.0
            categories.append(
                {
                    "category": row["category"],
                    "total_amount": round(cat_total, 2),
                    "total_inr": format_inr(cat_total),
                    "transaction_count": cat_count,
                    "percentage_of_total": pct,
                }
            )

        return {
            "year": valid_year,
            "month": valid_month,
            "month_name": month_name,
            "month_total_amount": month_total,
            "month_total_inr": format_inr(month_total),
            "total_transactions": total_transactions,
            "limit": limit_int,
            "categories": categories,
        }
    finally:
        conn.close()


def get_monthly_expenses(
    year: Optional[Any] = None,
    month: Optional[Any] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Retrieve all expense records for the specified month (or current month if omitted).

    Returns:
        Structured dictionary suitable for JSON serialization and resource exposure.
    """
    today = datetime.date.today()
    target_year = today.year if year is None else year
    target_month = today.month if month is None else month

    valid_year, valid_month = validate_month_year(target_year, target_month)
    month_prefix = f"{valid_year:04d}-{valid_month:02d}"
    month_name = calendar.month_name[valid_month]

    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT id, amount, category, description, expense_date, created_at
            FROM expenses
            WHERE substr(expense_date, 1, 7) = ?
            ORDER BY expense_date DESC, id DESC;
            """,
            (month_prefix,),
        )
        rows = cursor.fetchall()

        expenses: List[Dict[str, Any]] = []
        total_spending = 0.0
        for row in rows:
            amt = float(row["amount"])
            total_spending += amt
            expenses.append(
                {
                    "id": row["id"],
                    "amount": round(amt, 2),
                    "amount_inr": format_inr(amt),
                    "category": row["category"],
                    "description": row["description"],
                    "expense_date": row["expense_date"],
                    "created_at": row["created_at"],
                }
            )

        return {
            "year": valid_year,
            "month": valid_month,
            "month_name": month_name,
            "record_count": len(expenses),
            "total_amount": round(total_spending, 2),
            "total_inr": format_inr(total_spending),
            "expenses": expenses,
        }
    finally:
        conn.close()
