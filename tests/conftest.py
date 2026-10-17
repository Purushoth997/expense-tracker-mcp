"""Pytest configuration and fixtures for Expense Tracker MCP Server tests."""

from pathlib import Path
import tempfile
import pytest

from database import init_db


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Fixture providing an isolated temporary SQLite database path for each test."""
    db_file = tmp_path / "test_expenses.db"
    init_db(db_file)
    return db_file
