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


def build(scorecard_df, cohort_df, abc_df, delivery_df, output_dir):
    path = output_dir / "report.xlsx"
    wb = xlsxwriter.Workbook(str(path))
    wb.close()
    logger.info("Wrote Excel report: {}", path)
    return path
