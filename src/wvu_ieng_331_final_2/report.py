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

    # Write each KPI in its own column (B=1 through G=6, 0-indexed)
    for i, (label, value, vfmt) in enumerate(kpis):
        col_idx = 1 + i  # B=1, C=2, D=3, E=4, F=5, G=6
        ws.write(6, col_idx, label, kpi_label_fmt)
        ws.write(7, col_idx, value, vfmt)

    # ABC summary mini-table
    ws.set_row(9, 10)
    ws.set_row(10, 20)

    section_fmt = _fmt(
        wb,
        {
            "bold": True,
            "font_size": 11,
            "font_color": _NAVY,
            "bottom": 2,
            "bottom_color": _TEAL,
        },
    )
    ws.merge_range("B11:D11", "Product ABC Tier Summary", section_fmt)
    ws.merge_range("E11:G11", f"Best Delivery Corridor: {best_corridor}", section_fmt)

    tier_hdr = _fmt(
        wb,
        {
            "bold": True,
            "bg_color": _NAVY,
            "font_color": _WHITE,
            "align": "center",
            "border": 1,
            "border_color": _WHITE,
        },
    )
    tier_a = _fmt(
        wb,
        {
            "bg_color": _GREEN,
            "font_color": _WHITE,
            "align": "center",
            "border": 1,
            "bold": True,
            "font_size": 12,
        },
    )
    tier_b = _fmt(
        wb,
        {
            "bg_color": _ACCENT,
            "font_color": _WHITE,
            "align": "center",
            "border": 1,
            "bold": True,
            "font_size": 12,
        },
    )
    tier_c = _fmt(
        wb,
        {
            "bg_color": "#808080",
            "font_color": _WHITE,
            "align": "center",
            "border": 1,
            "bold": True,
            "font_size": 12,
        },
    )

    ws.set_row(11, 18)
    ws.set_row(12, 30)
    for col, hdr in zip(
        ["B", "C", "D"], ["Tier A (Top 80%)", "Tier B (Mid 15%)", "Tier C (Bot 5%)"]
    ):
        ws.write(f"{col}12", hdr, tier_hdr)
    ws.write("B13", f"{abc_a} products", tier_a)
    ws.write("C13", f"{abc_b} products", tier_b)
    ws.write("D13", f"{abc_c} products", tier_c)

    # Narrative
    ws.set_row(14, 10)
    narr_title = _fmt(
        wb,
        {
            "bold": True,
            "font_size": 12,
            "font_color": _NAVY,
            "bottom": 2,
            "bottom_color": _TEAL,
        },
    )
    narr_body = _fmt(
        wb,
        {"font_size": 10, "text_wrap": True, "valign": "top", "font_color": "#333333"},
    )
    bullet_fmt = _fmt(
        wb,
        {
            "font_size": 10,
            "text_wrap": True,
            "valign": "top",
            "font_color": _DARK,
            "indent": 1,
        },
    )

    ws.set_row(15, 18)
    ws.merge_range("B16:G16", "Executive Summary & Key Findings", narr_title)

    insights = [
        (
            "Seller Performance",
            "The composite scorecard (30% revenue, 30% on-time, 25% review score, 15% low cancellation) "
            "reveals wide variation across Brazil's 27 states. São Paulo (SP) dominates by volume, but "
            "smaller states often outperform on quality metrics. See the Seller Scorecard sheet for ranked detail.",
        ),
        (
            "Customer Retention",
            "Olist's 30-day repeat-purchase rate is critically low across all cohorts."
            "The Cohort Retention sheet shows how retention evolves over time "
            "and highlights which cohort months had the strongest early re-engagement.",
        ),
        (
            "Product Portfolio (ABC)",
            f"Only {abc_a} products (Tier A) drive the top 80% of revenue. "
            f"The remaining {abc_b + abc_c} products (Tiers B & C) contribute marginally. "
            "Sellers and category managers should focus inventory and marketing on Tier A products.",
        ),
        (
            "Delivery Performance",
            "Delivery corridors vary substantially in on-time rate. Intra-state shipments generally "
            "outperform cross-state routes. Corridors with late delivery directly correlate with lower "
            "review scores, suggesting logistics investment would yield measurable customer experience gains.",
        ),
        (
            "Recommendations",
            "① Audit the bottom sellers for corrective action or removal. "
            "② Launch a re-engagement campaign targeting cohorts with low retention. "
            "③ Negotiate with carriers on the worst-performing delivery corridors. "
            "④ Rationalize the Tier C product catalog to reduce operational overhead.",
        ),
    ]

    row = 16
    for title, body in insights:
        ws.set_row(row, 14)
        bullet_title = _fmt(wb, {"bold": True, "font_size": 10, "font_color": _TEAL})
        ws.write(row, 1, f"▸ {title}", bullet_title)
        ws.set_row(row + 1, 52)
        ws.merge_range(row + 1, 1, row + 1, 6, body, narr_body)
        row += 2

    # Footer
    footer_fmt = _fmt(
        wb,
        {
            "font_size": 8,
            "font_color": "#888888",
            "align": "center",
            "italic": True,
            "top": 1,
            "top_color": _LIGHT,
        },
    )
    ws.set_row(row + 1, 18)
    ws.merge_range(
        row + 1,
        1,
        row + 1,
        6,
        "Data source: Olist public e-commerce dataset · Analysis period: full dataset · "
        "Pipeline: wvu-ieng-331-final-2",
        footer_fmt,
    )


def build(scorecard_df, cohort_df, abc_df, delivery_df, output_dir):
    path = output_dir / "report.xlsx"
    wb = xlsxwriter.Workbook(str(path))
    _write_cover(
        wb, scorecard_df, cohort_df, abc_df, delivery_df
    )  # ← this line must be here
    wb.close()
    logger.info("Wrote Excel report: {}", path)
    return path
