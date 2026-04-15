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
    con = _connect(db_path)
    try:
        rows = con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main'"
        ).fetchall()
        found = {r[0] for r in rows}
        missing = EXPECTED_TABLES - found
        if missing:
            logger.warning(
                "Missing tables: {}. Expected {} but found {}.",
                sorted(missing),
                len(EXPECTED_TABLES),
                len(found),
            )
            return False
        logger.info("Table existence check passed ({} tables found).", len(found))
        return True
    finally:
        con.close()


def check_key_columns_not_null(db_path: str | Path) -> bool:
    """Verify that key ID columns are not entirely NULL.

    Checks order_id, customer_id, product_id, and seller_id across the
    tables where they are meaningful primary or foreign keys.

    Args:
        db_path: Path to the DuckDB database file.

    Returns:
        ``True`` if no key column is entirely NULL, ``False`` otherwise.
    """
    con = _connect(db_path)
    all_ok = True
    try:
        for table, columns in KEY_COLUMNS.items():
            for col in columns:
                try:
                    (count,) = con.execute(
                        f"SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL"
                    ).fetchone()  # type: ignore[misc]
                    if count == 0:
                        logger.warning(
                            "Column '{}.{}' is entirely NULL – no usable keys.",
                            table,
                            col,
                        )
                        all_ok = False
                    else:
                        logger.info(
                            "Key column '{}.{}' has {} non-null values.",
                            table,
                            col,
                            count,
                        )
                except duckdb.Error as exc:
                    logger.warning("Could not check '{}.{}': {}", table, col, exc)
                    all_ok = False
    finally:
        con.close()
    return all_ok


def check_date_range(db_path: str | Path) -> bool:
    """Verify that order purchase timestamps are within a reasonable window.

    Checks that the date range is non-empty, that the earliest order is not
    suspiciously old (before 2016-01-01), and that no orders are future-dated.
    Future-dated orders log a WARNING but the check still returns True so the
    pipeline can continue – the holdout dataset legitimately extends beyond today.

    Args:
        db_path: Path to the DuckDB database file.

    Returns:
        ``True`` if the date range is non-empty and the minimum date is
        plausible, ``False`` otherwise.
    """
    con = _connect(db_path)
    try:
        row = con.execute(
            "SELECT MIN(order_purchase_timestamp), MAX(order_purchase_timestamp) "
            "FROM orders"
        ).fetchone()
        if row is None or row[0] is None:
            logger.warning("orders table has no rows – date range check skipped.")
            return False

        min_ts, max_ts = row

        def _to_date(val: object) -> date:
            """Normalise a DuckDB timestamp return value to ``datetime.date``.

            Args:
                val: A ``datetime``, ``date``, or ISO-format ``str`` as returned
                    by DuckDB depending on driver version.

            Returns:
                The corresponding ``datetime.date`` object.

            Raises:
                TypeError: If ``val`` is not a recognised type.
            """
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, date):
                return val
            if isinstance(val, str):
                return datetime.fromisoformat(val).date()
            raise TypeError(f"Cannot convert {type(val)} to date")

        min_date = _to_date(min_ts)
        max_date = _to_date(max_ts)
        today = date.today()

        if min_date < DATE_RANGE_EARLIEST:
            logger.warning(
                "Earliest order date {} is before expected threshold {} – "
                "data may be corrupted or from a different dataset.",
                min_date,
                DATE_RANGE_EARLIEST,
            )
            return False

        if max_date > today:
            logger.warning(
                "Latest order date {} is beyond today ({}) – "
                "dataset contains future-dated records (extended holdout data).",
                max_date,
                today,
            )

        logger.info(
            "Date range check passed: {} – {} ({} calendar days).",
            min_date,
            max_date,
            (max_date - min_date).days,
        )
        return True
    finally:
        con.close()


def check_row_counts(db_path: str | Path) -> bool:
    """Verify that table has more rows than minimum row-count thresholds.

    Thresholds are defined in ``MIN_ROW_COUNTS`` (1,000 rows each for
    orders, order_items, and customers).  A threshold of 1,000 was chosen
    because the Olist dataset contains ~100 k orders, anything below 1,000
    suggests messed up data.

    Args:
        db_path: Path to the DuckDB database file.

    Returns:
        ``True`` if all tables exceed their threshold, ``False`` otherwise.
    """
    con = _connect(db_path)
    all_ok = True
    try:
        for table, minimum in MIN_ROW_COUNTS.items():
            try:
                (count,) = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()  # type: ignore[misc]
                if count < minimum:
                    logger.warning(
                        "Table '{}' has {} rows, below minimum threshold of {}.",
                        table,
                        count,
                        minimum,
                    )
                    all_ok = False
                else:
                    logger.info(
                        "Row count check passed for '{}': {} rows.", table, count
                    )
            except duckdb.Error as exc:
                logger.warning("Could not count rows in '{}': {}", table, exc)
                all_ok = False
    finally:
        con.close()
    return all_ok
