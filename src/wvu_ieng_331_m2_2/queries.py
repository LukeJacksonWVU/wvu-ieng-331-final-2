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
