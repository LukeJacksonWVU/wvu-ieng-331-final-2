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
