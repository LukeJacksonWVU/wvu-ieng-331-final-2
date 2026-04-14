from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import duckdb
from loguru import logger

# ---------------------------------------------------------------------------
# Expected schema
# ---------------------------------------------------------------------------
EXPECTED_TABLES: set[str] = {
    "category_translation",
    "customers",
    "geolocation",
    "order_items",
    "order_payments",
    "order_reviews",
    "orders",
    "products",
    "sellers",
}

KEY_COLUMNS: dict[str, list[str]] = {
    "orders": ["order_id", "customer_id"],
    "order_items": ["order_id", "product_id", "seller_id"],
    "customers": ["customer_id"],
    "products": ["product_id"],
    "sellers": ["seller_id"],
}

MIN_ROW_COUNTS: dict[str, int] = {
    "orders": 1_000,
    "order_items": 1_000,
    "customers": 1_000,
}

# Olist data set start to end (new data included)
DATE_RANGE_EARLIEST: date = date(2016, 1, 1)


def _connect(db_path: str | Path) -> duckdb.DuckDBPyConnection:
    """Open a read-only DuckDB connection.

    Args:
        db_path: Path to the DuckDB database file.

    Returns:
        An open DuckDB connection.

    Raises:
        FileNotFoundError: [path] If the database file does not exist.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    return duckdb.connect(str(db_path), read_only=True)

    def check_tables_exist(db_path: str | Path) -> bool:
        """Verify that all 9 expected tables are present in the database.

        Args:
            db_path: Path to the DuckDB database file.

        Returns:
            ``True`` if all tables exist, ``False`` otherwise.
        """
