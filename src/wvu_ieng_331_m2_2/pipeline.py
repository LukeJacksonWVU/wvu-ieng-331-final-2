"""Pipeline orchestration script.

Entry point for the Milestone 2 analysis pipeline.  Accepts CLI parameters,
runs validation, executes queries, writes output files, and produces a chart.

Usage examples::

    uv run wvu-ieng-331-m2
    uv run wvu-ieng-331-m2 --start-date 2017-01-01 --end-date 2018-12-31
    uv run wvu-ieng-331-m2 --seller-state SP
    uv run wvu-ieng-331-m2 --db-path /path/to/olist.duckdb --seller-state RJ
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import altair as alt
import duckdb
import polars as pl
from loguru import logger

from wvu_ieng_331_m2_2 import queries, validation

# Default database path (relative to the project root, two levels above src/)
_DEFAULT_DB = Path(__file__).parent.parent.parent / "data" / "olist.duckdb"
_DEFAULT_OUTPUT = Path(__file__).parent.parent.parent / "output"


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Parsed namespace with attributes: db_path, start_date, end_date,
        seller_state, halt_on_validation_failure.
    """
    parser = argparse.ArgumentParser(
        prog="wvu-ieng-331-m2",
        description="Olist e-commerce analysis pipeline (WVU IENG 331 Milestone 2).",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=_DEFAULT_DB,
        help="Path to the olist.duckdb file (default: data/olist.duckdb).",
    )
    parser.add_argument(
        "--start-date",
        type=date.fromisoformat,
        default=None,
        metavar="YYYY-MM-DD",
        help="Inclusive start date filter on order_purchase_timestamp.",
    )
    parser.add_argument(
        "--end-date",
        type=date.fromisoformat,
        default=None,
        metavar="YYYY-MM-DD",
        help="Inclusive end date filter on order_purchase_timestamp.",
    )
    parser.add_argument(
        "--seller-state",
        type=str,
        default=None,
        metavar="XX",
        help="Two-letter Brazilian state abbreviation to filter sellers (e.g. SP).",
    )
    parser.add_argument(
        "--halt-on-validation-failure",
        action="store_true",
        default=False,
        help="Halt the pipeline if any validation check fails (default: warn and continue).",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _ensure_output_dir(output_dir: Path) -> None:
    """Creates the output directory if it does not exist.

    Args:
        output_dir: Path to the desired output directory.

    Returns:
        None

    Raises:
        OSError: If the directory cannot be created.
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Output directory ready: {}", output_dir)
    except OSError as exc:
        logger.error("Cannot create output directory {}: {}", output_dir, exc)
        raise


def _write_summary_csv(df: pl.DataFrame, output_dir: Path) -> None:
    """Write the summary DataFrame to summary.csv.

    Args:
        df: Aggregated summary-level DataFrame.
        output_dir: Directory in which to write the file.

    Returns:
        None

    Raises:
        OSError: If the file cannot be written.
    """
    path = output_dir / "summary.csv"
    try:
        df.write_csv(path)
        logger.info("Wrote summary CSV: {} ({} rows)", path, len(df))
    except OSError as exc:
        logger.error("Failed to write {}: {}", path, exc)
        raise


def _write_detail_parquet(df: pl.DataFrame, output_dir: Path) -> None:
    """Writes the detail DataFrame to detail.parquet.

    Args:
        df: Full scored/classified detail-level DataFrame.
        output_dir: Directory in which to write the file.

    Returns:
        None

    Raises:
        OSError: If the file cannot be written.
    """
    path = output_dir / "detail.parquet"
    try:
        df.write_parquet(path)
        logger.info("Wrote detail Parquet: {} ({} rows)", path, len(df))
    except OSError as exc:
        logger.error("Failed to write {}: {}", path, exc)
        raise


def _write_chart_html(df: pl.DataFrame, output_dir: Path) -> None:
    """Builds an Altair chart and save it as a self-contained HTML file.

    The chart shows average composite score by seller state, making it easy
    to spot which states have the strongest and weakest seller performance and compare from state to state.

    Args:
        df: Seller scorecard DataFrame returned by ``queries.get_seller_scorecard``.
        output_dir: Directory in which to write chart.html.

    Returns:
        None

    Raises:
        OSError: If the file cannot be written.
        ValueError: If the DataFrame is missing expected columns.
    """
    required = {"seller_state", "composite_score", "total_revenue"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Seller scorecard missing columns for chart: {missing}")

    # Aggregate: mean composite score and total revenue per state
    summary = (
        df.group_by("seller_state")
        .agg(
            pl.col("composite_score").mean().alias("avg_composite_score"),
            pl.col("total_revenue").sum().alias("total_revenue"),
            pl.len().alias("seller_count"),
        )
        .sort("avg_composite_score", descending=True)
    )

    chart = (
        alt.Chart(summary)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(
                "seller_state:N",
                sort="-y",
                axis=alt.Axis(title="Seller State"),
            ),
            y=alt.Y(
                "avg_composite_score:Q",
                axis=alt.Axis(title="Avg Composite Score"),
            ),
            color=alt.Color(
                "total_revenue:Q",
                scale=alt.Scale(scheme="blues"),
                legend=alt.Legend(title="Total Revenue (BRL)"),
            ),
            tooltip=[
                alt.Tooltip("seller_state:N", title="State"),
                alt.Tooltip("avg_composite_score:Q", title="Avg Score", format=".3f"),
                alt.Tooltip("total_revenue:Q", title="Total Revenue", format=",.0f"),
                alt.Tooltip("seller_count:Q", title="# Sellers"),
            ],
        )
        .properties(
            title="Average Seller Composite Score by State",
            width=700,
            height=400,
        )
    )

    path = output_dir / "chart.html"
    try:
        # Write an HTML file without vl-convert-python.
        # Embeds the Vega-Embed JS from CDN and the chart spec as JSON.
        spec_json = chart.to_json()
        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Seller Composite Score by State</title>
  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
  <style>body {{ font-family: sans-serif; padding: 2rem; }}</style>
</head>
<body>
  <div id="chart"></div>
  <script>
    vegaEmbed("#chart", {spec_json});
  </script>
</body>
</html>"""
        path.write_text(html, encoding="utf-8")
        logger.info("Wrote Altair chart: {}", path)
    except OSError as exc:
        logger.error("Failed to write {}: {}", path, exc)
        raise


# ---------------------------------------------------------------------------
# Pipeline stages
# ---------------------------------------------------------------------------


def _build_summary(
    scorecard_df: pl.DataFrame,
    abc_df: pl.DataFrame,
    cohort_df: pl.DataFrame,
) -> pl.DataFrame:
    """Aggregate state-level summary metrics for summary.csv.

    Combines top-line metrics from the seller scorecard, ABC tier breakdown,
    and the most recent cohort's 30-day retention rate into a single row-per-state
    summary table.

    Args:
        scorecard_df: Full seller scorecard DataFrame.
        abc_df: Product-level ABC classification DataFrame.
        cohort_df: Monthly cohort retention DataFrame.

    Returns:
        Aggregated summary DataFrame (one row per seller state).
    """
    state_summary = (
        scorecard_df.group_by("seller_state")
        .agg(
            pl.len().alias("seller_count"),
            pl.col("total_revenue").sum().alias("state_total_revenue"),
            pl.col("composite_score").mean().round(4).alias("avg_composite_score"),
            pl.col("on_time_rate_pct").mean().round(2).alias("avg_on_time_rate_pct"),
            pl.col("avg_review_score").mean().round(2).alias("avg_review_score"),
        )
        .sort("state_total_revenue", descending=True)
    )

    # ABC tier counts (global, not per-state – attach once)
    _abc_tier_df = abc_df.group_by("abc_tier").agg(pl.len().alias("product_count"))
    abc_counts: dict[str, int] = dict(
        zip(_abc_tier_df["abc_tier"].to_list(), _abc_tier_df["product_count"].to_list())
    )
    state_summary = state_summary.with_columns(
        pl.lit(abc_counts.get("A", 0)).alias("abc_a_products"),
        pl.lit(abc_counts.get("B", 0)).alias("abc_b_products"),
        pl.lit(abc_counts.get("C", 0)).alias("abc_c_products"),
    )

    # Most recent cohort retention
    if len(cohort_df) > 0:
        latest_retention = float(
            cohort_df.sort("cohort_month", descending=True)
            .head(1)["retention_rate_30d"]
            .item()
        )
        state_summary = state_summary.with_columns(
            pl.lit(latest_retention).alias("latest_cohort_retention_30d_pct")
        )

    return state_summary


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run the full analysis pipeline.

    Workflow: validate → query → process → write outputs.

    Args:
        argv: Optional argument list for testing (defaults to sys.argv[1:]).

    Returns:
        Exit code: ``0`` on success, ``1`` on error.
    """
    args = _parse_args(argv)

    logger.info("=== WVU IENG 331 Milestone 2 Pipeline ===")
    logger.info(
        "Parameters: db={}, start_date={}, end_date={}, seller_state={}",
        args.db_path,
        args.start_date,
        args.end_date,
        args.seller_state,
    )

    # ---- 1. Validate -------------------------------------------------------
    logger.info("Step 1/4 – Running validation…")
    try:
        validation.run_all(
            args.db_path,
            halt_on_failure=args.halt_on_validation_failure,
        )
    except FileNotFoundError as exc:
        logger.error(
            "Database file not found: {}. "
            "Place olist.duckdb in the data/ directory or pass --db-path.",
            exc,
        )
        return 1
    except RuntimeError as exc:
        logger.error("Validation halted pipeline: {}", exc)
        return 1

    # ---- 2. Query ----------------------------------------------------------
    logger.info("Step 2/4 – Executing queries…")
    try:
        scorecard_df = queries.get_seller_scorecard(
            args.db_path,
            seller_state=args.seller_state,
            start_date=args.start_date,
            end_date=args.end_date,
        )
        logger.info("Seller scorecard: {} rows", len(scorecard_df))

        abc_df = queries.get_abc_classification(
            args.db_path,
            start_date=args.start_date,
            end_date=args.end_date,
        )
        logger.info("ABC classification: {} products", len(abc_df))

        cohort_df = queries.get_cohort_retention(
            args.db_path,
            start_date=args.start_date,
            end_date=args.end_date,
        )
        logger.info("Cohort retention: {} cohorts", len(cohort_df))

        delivery_df = queries.get_delivery_time_analysis(
            args.db_path,
            seller_state=args.seller_state,
            start_date=args.start_date,
            end_date=args.end_date,
        )
        logger.info("Delivery analysis: {} corridors", len(delivery_df))

    except FileNotFoundError as exc:
        logger.error("Database not found during query phase: {}", exc)
        return 1
    except duckdb.Error as exc:
        logger.error("Query failed: {}", exc)
        return 1

    # ---- 3. Process --------------------------------------------------------
    logger.info("Step 3/4 – Aggregating outputs…")
    try:
        summary_df = _build_summary(scorecard_df, abc_df, cohort_df)
        # detail.parquet = every product with ABC tier, revenue %, and cumulative %
        detail_df = abc_df
    except ValueError as exc:
        logger.error("Data processing error: {}", exc)
        return 1

    # ---- 4. Write outputs --------------------------------------------------
    logger.info("Step 4/4 – Writing output files…")
    try:
        _ensure_output_dir(_DEFAULT_OUTPUT)
        _write_summary_csv(summary_df, _DEFAULT_OUTPUT)
        _write_detail_parquet(detail_df, _DEFAULT_OUTPUT)
        _write_chart_html(scorecard_df, _DEFAULT_OUTPUT)
    except OSError as exc:
        logger.error("Output write failure: {}", exc)
        return 1
    except ValueError as exc:
        logger.error("Chart build error: {}", exc)
        return 1

    logger.info("=== Pipeline complete. Outputs in: {} ===", _DEFAULT_OUTPUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
