"""Unit tests for the SQLite database layer of Expense Tracker."""

import datetime
from pathlib import Path
import pytest

from database import (
    add_expense,
    format_inr,
    get_monthly_expenses,
    get_monthly_total,
    get_top_categories,
    init_db,
    validate_expense_input,
    validate_month_year,
)


def test_add_expense_success(temp_db_path: Path):
    """Test 1: Successfully adding an expense to the database."""
    result = add_expense(
        amount=250.75,
        category="Food",
        description="Lunch at cafeteria",
        expense_date="2026-10-17",
        db_path=temp_db_path,
    )

    assert result["id"] is not None
    assert result["id"] >= 1
    assert result["amount"] == 250.75
    assert result["amount_inr"] == "₹250.75"
    assert result["category"] == "Food"
    assert result["description"] == "Lunch at cafeteria"
    assert result["expense_date"] == "2026-10-17"
    assert result["created_at"] != ""


def test_add_expense_default_date(temp_db_path: Path):
    """Test adding an expense without specifying date defaults to today."""
    today_iso = datetime.date.today().isoformat()
    result = add_expense(
        amount=50.0,
        category="Transport",
        description="Bus ticket",
        expense_date=None,
        db_path=temp_db_path,
    )
    assert result["expense_date"] == today_iso


def test_monthly_total_calculation(temp_db_path: Path):
    """Test 2: Correct monthly total and transaction count calculation."""
    # Add expenses for October 2026
    add_expense(150.00, "Food", "Breakfast", "2026-10-01", db_path=temp_db_path)
    add_expense(350.50, "Transport", "Cab ride", "2026-10-10", db_path=temp_db_path)
    add_expense(500.00, "Food", "Groceries", "2026-10-15", db_path=temp_db_path)

    # Add expense for a different month (November 2026) to ensure separation
    add_expense(1000.00, "Shopping", "Winter jacket", "2026-11-02", db_path=temp_db_path)

    october_summary = get_monthly_total(year=2026, month=10, db_path=temp_db_path)
    assert october_summary["year"] == 2026
    assert october_summary["month"] == 10
    assert october_summary["month_name"] == "October"
    assert october_summary["total_amount"] == 1000.50
    assert october_summary["total_inr"] == "₹1,000.50"
    assert october_summary["transaction_count"] == 3

    november_summary = get_monthly_total(year=2026, month=11, db_path=temp_db_path)
    assert november_summary["total_amount"] == 1000.00
    assert november_summary["transaction_count"] == 1


def test_category_ranking(temp_db_path: Path):
    """Test 3: Correct category grouping, ranking in descending order, and percentage."""
    # Add expenses with multiple categories
    add_expense(300.00, "Food", "Lunch", "2026-10-05", db_path=temp_db_path)
    add_expense(700.00, "Food", "Dinner", "2026-10-06", db_path=temp_db_path)  # Food total: 1000
    add_expense(500.00, "Transport", "Train", "2026-10-07", db_path=temp_db_path)  # Transport total: 500
    add_expense(200.00, "Entertainment", "Movie", "2026-10-08", db_path=temp_db_path)  # Entertainment total: 200
    add_expense(100.00, "Education", "Books", "2026-10-09", db_path=temp_db_path)  # Education total: 100

    ranking = get_top_categories(year=2026, month=10, limit=3, db_path=temp_db_path)
    assert ranking["year"] == 2026
    assert ranking["month"] == 10
    assert ranking["month_total_amount"] == 1800.00
    assert ranking["total_transactions"] == 5

    categories = ranking["categories"]
    assert len(categories) == 3  # limited to 3

    # Rank 1: Food
    assert categories[0]["category"] == "Food"
    assert categories[0]["total_amount"] == 1000.00
    assert categories[0]["transaction_count"] == 2
    assert categories[0]["percentage_of_total"] == round((1000 / 1800) * 100, 1)

    # Rank 2: Transport
    assert categories[1]["category"] == "Transport"
    assert categories[1]["total_amount"] == 500.00
    assert categories[1]["transaction_count"] == 1

    # Rank 3: Entertainment
    assert categories[2]["category"] == "Entertainment"
    assert categories[2]["total_amount"] == 200.00
    assert categories[2]["transaction_count"] == 1


def test_invalid_expense_amounts_and_dates(temp_db_path: Path):
    """Test 4: Input validation properly rejects zero, negative, invalid amounts, and bad dates."""
    # Zero amount
    with pytest.raises(ValueError, match="positive number greater than 0"):
        add_expense(0, "Food", "Snack", db_path=temp_db_path)

    # Negative amount
    with pytest.raises(ValueError, match="positive number greater than 0"):
        add_expense(-50.0, "Food", "Refund", db_path=temp_db_path)

    # Non-numeric string amount
    with pytest.raises(ValueError, match="valid positive number"):
        add_expense("abc", "Food", "Lunch", db_path=temp_db_path)

    # None amount
    with pytest.raises(ValueError, match="Amount is required"):
        add_expense(None, "Food", "Lunch", db_path=temp_db_path)

    # Empty category
    with pytest.raises(ValueError, match="Category is required"):
        add_expense(100.0, "", "Lunch", db_path=temp_db_path)

    with pytest.raises(ValueError, match="Category is required"):
        add_expense(100.0, "   ", "Lunch", db_path=temp_db_path)

    # Empty description
    with pytest.raises(ValueError, match="Description is required"):
        add_expense(100.0, "Food", "", db_path=temp_db_path)

    with pytest.raises(ValueError, match="Description is required"):
        add_expense(100.0, "Food", "   ", db_path=temp_db_path)

    # Invalid date format
    with pytest.raises(ValueError, match="Invalid date format"):
        add_expense(100.0, "Food", "Lunch", expense_date="17-10-2026", db_path=temp_db_path)

    # Invalid calendar date (e.g., February 31)
    with pytest.raises(ValueError, match="Invalid calendar date"):
        add_expense(100.0, "Food", "Lunch", expense_date="2026-02-31", db_path=temp_db_path)


def test_empty_database_behavior(temp_db_path: Path):
    """Test 5: Correct behavior when querying an empty database."""
    # Monthly total on empty DB
    total_data = get_monthly_total(year=2026, month=10, db_path=temp_db_path)
    assert total_data["total_amount"] == 0.0
    assert total_data["total_inr"] == "₹0.00"
    assert total_data["transaction_count"] == 0

    # Top categories on empty DB
    top_data = get_top_categories(year=2026, month=10, db_path=temp_db_path)
    assert top_data["month_total_amount"] == 0.0
    assert top_data["total_transactions"] == 0
    assert top_data["categories"] == []

    # Monthly expenses resource list on empty DB
    exp_data = get_monthly_expenses(year=2026, month=10, db_path=temp_db_path)
    assert exp_data["record_count"] == 0
    assert exp_data["total_amount"] == 0.0
    assert exp_data["expenses"] == []


def test_invalid_month_year_validation():
    """Test validation of month and year inputs."""
    with pytest.raises(ValueError, match="Month must be an integer between 1 and 12"):
        validate_month_year(2026, 0)

    with pytest.raises(ValueError, match="Month must be an integer between 1 and 12"):
        validate_month_year(2026, 13)

    with pytest.raises(ValueError, match="Year .* out of range"):
        validate_month_year(1850, 5)

    with pytest.raises(ValueError, match="Invalid year"):
        validate_month_year("not-a-year", 5)


def test_format_inr():
    """Test Indian Rupee formatting with various numerical values."""
    assert format_inr(0) == "₹0.00"
    assert format_inr(250) == "₹250.00"
    assert format_inr(1250.5) == "₹1,250.50"
    assert format_inr(99999) == "₹99,999.00"
    assert format_inr(100000) == "₹1,00,000.00"
    assert format_inr(10000000) == "₹1,00,00,000.00"
