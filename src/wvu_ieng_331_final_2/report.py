"""Report generation module."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import xlsxwriter
from loguru import logger

# Palette

_NAVY = "#1F3864"
_TEAL = "#2E75B6"
_LIGHT = "#D6E4F0"
_ACCENT = "#ED7D31"
_GREEN = "#70AD47"
_WHITE = "#FFFFFF"
_GREY = "#F2F2F2"
_DARK = "#1A1A2E"
_FONT = "Arial"


def _fmt(wb: xlsxwriter.Workbook, props: dict) -> xlsxwriter.workbook.Format:
    base = {"font_name": _FONT, "font_size": 10}
    base.update(props)
    return wb.add_format(base)


# Cover Sheet
def _write_cover(
    wb: xlsxwriter.Workbook,
    scorecard_df: pl.DataFrame,
    cohort_df: pl.DataFrame,
    abc_df: pl.DataFrame,
    delivery_df: pl.DataFrame,
) -> None:
    ws = wb.add_worksheet("Cover")
    ws.set_tab_color(_NAVY)
    ws.hide_gridlines(2)
    ws.set_column("A:A", 3)
    ws.set_column("B:B", 28)
    ws.set_column("C:H", 18)
    # Title banner
    title_fmt = _fmt(
        wb,
        {
            "bold": True,
            "font_size": 22,
            "font_color": _WHITE,
            "bg_color": _NAVY,
            "align": "center",
            "valign": "vcenter",
            "border": 0,
        },
    )
    sub_fmt = _fmt(
        wb,
        {
            "font_size": 12,
            "font_color": _LIGHT,
            "bg_color": _NAVY,
            "align": "center",
            "valign": "vcenter",
        },
    )

    ws.set_row(0, 6)
    ws.merge_range("A1:H1", "", _fmt(wb, {"bg_color": _NAVY}))
    ws.set_row(1, 50)
    ws.merge_range("A2:H2", "Olist E-Commerce - Business Performance Report", title_fmt)
    ws.set_row(2, 24)
    ws.merge_range(
        "A3:H3",
        "WVU IENG 331 - Team 2 - Luke Jackson, Gavin Miller, William Muhly",
        sub_fmt,
    )
    ws.set_row(3, 6)
    ws.merge_range("A4:H4", "", _fmt(wb, {"bg_color": _NAVY}))

    # KPI tiles
    # Use columns B-G with each KPI occupying one full column (no merging needed)
    kpi_label_fmt = _fmt(
        wb,
        {
            "bold": True,
            "font_size": 9,
            "font_color": _WHITE,
            "bg_color": _TEAL,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "border_color": _WHITE,
        },
    )
    kpi_value_fmt = _fmt(
        wb,
        {
            "bold": True,
            "font_size": 16,
            "font_color": _DARK,
            "bg_color": _LIGHT,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "border_color": _TEAL,
        },
    )
    kpi_value_pct_fmt = _fmt(
        wb,
        {
            "bold": True,
            "font_size": 16,
            "font_color": _DARK,
            "bg_color": _LIGHT,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "border_color": _TEAL,
            "num_format": "0.0%",
        },
    )
    kpi_value_cur_fmt = _fmt(
        wb,
        {
            "bold": True,
            "font_size": 16,
            "font_color": _DARK,
            "bg_color": _LIGHT,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "border_color": _TEAL,
            "num_format": "R#,##0",
        },
    )

    # Compute KPIs
    total_sellers = len(scorecard_df)
    total_revenue = float(scorecard_df["total_revenue"].sum())
    avg_score = float(scorecard_df["composite_score"].mean())
    avg_review = float(scorecard_df["avg_review_score"].mean())
    avg_ontime = float(scorecard_df["on_time_rate_pct"].mean()) / 100.0
    latest_retention = 0.0
    if len(cohort_df) > 0:
        latest_retention = (
            float(
                cohort_df.sort("cohort_month", descending=True)
                .head(1)["retention_rate_30d"]
                .item()
            )
            / 100.0
        )
    abc_a = len(abc_df.filter(pl.col("abc_tier") == "A"))
    abc_b = len(abc_df.filter(pl.col("abc_tier") == "B"))
    abc_c = len(abc_df.filter(pl.col("abc_tier") == "C"))
    top_corridors = delivery_df.sort("on_time_rate_pct", descending=True).head(1)
    best_corridor = (
        top_corridors["corridor"].item() if len(top_corridors) > 0 else "N/A"
    )

    kpis = [
        ("Total Sellers", total_sellers, kpi_value_fmt),
        ("Total Revenue (BRL)", total_revenue, kpi_value_cur_fmt),
        ("Avg Composite Score", avg_score, kpi_value_fmt),
        ("Avg Review Score", avg_review, kpi_value_fmt),
        ("Avg On-Time Delivery", avg_ontime, kpi_value_pct_fmt),
        ("30-Day Retention Rate", latest_retention, kpi_value_pct_fmt),
    ]

    ws.set_row(5, 10)
    ws.set_row(6, 22)
    ws.set_row(7, 44)


def build(scorecard_df, cohort_df, abc_df, delivery_df, output_dir):
    path = output_dir / "report.xlsx"
    wb = xlsxwriter.Workbook(str(path))
    wb.close()
    logger.info("Wrote Excel report: {}", path)
    return path
