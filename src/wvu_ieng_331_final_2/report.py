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


def build(scorecard_df, cohort_df, abc_df, delivery_df, output_dir):
    path = output_dir / "report.xlsx"
    wb = xlsxwriter.Workbook(str(path))
    wb.close()
    logger.info("Wrote Excel report: {}", path)
    return path
