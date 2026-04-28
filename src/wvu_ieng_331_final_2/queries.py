"""Data access module.

Reads SQL files from the sql/ directory and executes them against DuckDB,
returning Polars DataFrames.  No inline SQL appears in this file.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb
import polars as pl

# Resolve the sql/ directory relative to this file's location:
# src/wvu_ieng_331_m2/queries.py  →  ../../sql/
_SQL_DIR = Path(__file__).parent.parent.parent / "sql"
#helpers

def _load_sql(filename: str) -> str:
    """Read a SQL file from the sql/ directory.

    Args:
        filename: Name of the .sql file (e.g. ``'seller_scorecard.sql'``).

    Returns:
        The raw SQL string.

    Raises:
        FileNotFoundError: If the SQL file does not exist.
    """
    # build path and verify oyutput
    path = _SQL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8")


def _execute(
    db_path: str | Path,
    sql: str,
    params: list | None = None,
) -> pl.DataFrame:
    """Execute a parameterized SQL query against DuckDB and return a Polars DataFrame.

    Args:
        db_path: Path to the DuckDB database file.
        sql: Parameterized SQL string (uses ``$1``, ``$2`` placeholders).
        params: Ordered list of parameter values to bind.

    Returns:
        Query results as a Polars DataFrame.

    Raises:
        FileNotFoundError: If the database file does not exist.
        duckdb.Error: If the query fails.
    """
    # verify db file exists
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    # open read-only and close
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        result = con.execute(sql, params or []).fetchall()
        columns = [desc[0] for desc in con.description]  # type: ignore[union-attr]
        return pl.DataFrame(result, schema=columns, orient="row")
    finally:
        con.close()
# ---------------------------------------------------------------------------
# public query functions
# ---------------------------------------------------------------------------


def get_seller_scorecard(
    db_path: str | Path,
    seller_state: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> pl.DataFrame:
    """Return the seller scorecard with composite performance scores.

    Args:
        db_path: Path to the DuckDB database file.
        seller_state: Two-letter state abbreviation to filter by (e.g. ``'SP'``).
            ``None`` returns all states.
        start_date: Inclusive lower bound on order purchase date.
        end_date: Inclusive upper bound on order purchase date.

    Returns:
        DataFrame with columns: seller_id, seller_city, seller_state,
        total_orders, total_revenue, on_time_rate_pct, avg_review_score,
        cancellation_rate_pct, composite_score, seller_rank.
    """
    # load and ex. seller scorecard
    sql = _load_sql("seller_scorecard.sql")
    return _execute(db_path, sql, [seller_state, start_date, end_date])


def get_abc_classification(
    db_path: str | Path,
    start_date: date | None = None,
    end_date: date | None = None,
) -> pl.DataFrame:
    """Return product-level ABC revenue classification.

    Args:
        db_path: Path to the DuckDB database file.
        start_date: Inclusive lower bound on order purchase date.
        end_date: Inclusive upper bound on order purchase date.

    Returns:
        DataFrame with columns: product_id, category, total_revenue,
        revenue_pct, cumulative_pct, abc_tier.
    """
    # load and ex abc class
    sql = _load_sql("abc_classification.sql")
    return _execute(db_path, sql, [start_date, end_date])


def get_cohort_retention(
    db_path: str | Path,
    start_date: date | None = None,
    end_date: date | None = None,
) -> pl.DataFrame:
    """Return monthly cohort retention rates at 30 / 60 / 90 days.

    Args:
        db_path: Path to the DuckDB database file.
        start_date: Inclusive lower bound on cohort first-order date.
        end_date: Inclusive upper bound on cohort first-order date.

    Returns:
        DataFrame with columns: cohort_month, cohort_size, returned_30d,
        retention_rate_30d, returned_60d, retention_rate_60d,
        returned_90d, retention_rate_90d.
    """
    # load and ex cohort retention
    sql = _load_sql("cohort_retention_analysis.sql")
    return _execute(db_path, sql, [start_date, end_date])


def get_delivery_time_analysis(
    db_path: str | Path,
    seller_state: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> pl.DataFrame:
    """Return corridor-level delivery time metrics.

    Args:
        db_path: Path to the DuckDB database file.
        seller_state: Two-letter state abbreviation to filter sellers.
            ``None`` includes all states.
        start_date: Inclusive lower bound on order purchase date.
        end_date: Inclusive upper bound on order purchase date.

    Returns:
        DataFrame with columns: corridor, total_deliveries, avg_actual_days,
        avg_estimated_days, avg_days_early_late, on_time_rate_pct, late_rate_pct,
        rank_best_corridors, rank_worst_corridors.
    """
    # load and ex delivery time
    
    sql = _load_sql("delivery_time_analysis.sql")
    return _execute(db_path, sql, [seller_state, start_date, end_date])
# --- Data Quality Functions ---


def get_row_counts(db_path: str | Path) -> pl.DataFrame:
    """Return row counts for all nine dataset tables.

    Args:
        db_path: Path to the DuckDB database file.

    Returns:
        DataFrame with columns: tableName, rowCount.
    """
    # counts all rows across all tables
    sql = _load_sql("row_count.sql")
    return _execute(db_path, sql)


def get_date_range(db_path: str | Path) -> pl.DataFrame:
    """Return the min/max order date and span statistics.

    Args:
        db_path: Path to the DuckDB database file.

    Returns:
        DataFrame with columns: firstOrderDate, lastOrderDate,
        PurchaseDays, calendarDays.
    """
    # scans the date range
    sql = _load_sql("date_range.sql")
    return _execute(db_path, sql)


def get_null_check(db_path: str | Path) -> pl.DataFrame:
    """Return per-table null percentages for key ID columns.

    Args:
        db_path: Path to the DuckDB database file.

    Returns:
        DataFrame with columns: tableName, totalRows, nullCustomerIdPercent,
        nullOrderIdPercent, nullProductIdPercent, nullSellerIdPercent.
    """
    # checks nulls
    sql = _load_sql("null_check.sql")
    return _execute(db_path, sql)


def get_duplicate_check(db_path: str | Path) -> pl.DataFrame:
    """Return duplicate key counts for orders, customers, and products.

    Args:
        db_path: Path to the DuckDB database file.

    Returns:
        DataFrame with columns: tableName, duplicateKeys, totalDuplicateRows.
    """
    # checks for duplicates
    sql = _load_sql("duplicate_check.sql")
    return _execute(db_path, sql)


def get_orphaned_keys(db_path: str | Path) -> pl.DataFrame:
    """Return orphaned foreign-key counts across core join paths.

    Args:
        db_path: Path to the DuckDB database file.

    Returns:
        DataFrame with columns: foreignKeys, orphan_count.
    """
    # checks join paths
    sql = _load_sql("orphaned_keys.sql")
    return _execute(db_path, sql)
