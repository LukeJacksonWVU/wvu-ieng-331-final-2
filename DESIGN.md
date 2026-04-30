# DESIGN.md — wvu-ieng-331-final-2

WVU IENG 331 · Team 2 · Luke Jackson, Gavin Miller, William Muhly

---

## Pipeline Architecture

The pipeline follows a linear five-step orchestration pattern managed entirely by `pipeline.py`:

1. **Validation** — schema and data quality checks before any queries run
2. **Query execution** — four independent queries run against DuckDB, each returning a Polars DataFrame
3. **Aggregation** — DataFrames are combined into summary and detail outputs
4. **File outputs** — CSV, Parquet, and interactive HTML chart written to `output/`
5. **Report generation** — Excel workbook built from all four DataFrames and written to `output/`

Each step is isolated. A failure in step 2 does not corrupt step 4 outputs from a previous run.

---

## Module Responsibilities

### queries.py
Single responsibility: read a SQL file from `sql/`, execute it against DuckDB with parameters, and return a Polars DataFrame. No business logic lives here. All SQL is in `.sql` files, not inline strings, so queries can be edited and tested independently of Python.

### validation.py
Runs before queries. Checks that the database file exists, all required tables are present, key columns are not null, and date fields are logically ordered. Validation failures log a warning by default so the pipeline can still produce partial output — pass `--halt-on-validation-failure` to make them fatal.

### pipeline.py
Orchestration only. Parses CLI arguments, calls validation, calls each query function, assembles outputs, and calls `report.build()`. No SQL and no formatting logic lives here.

### report.py
Builds the Excel deliverable. One function per sheet (`_write_cover`, `_write_scorecard`, `_write_cohort`, `_write_abc`, `_write_delivery`), all called from a single `build()` entry point. This keeps each sheet self-contained — modifying one sheet cannot break another.

---

## SQL Design Decisions

### Parameterization
All queries use `$1`, `$2`, `$3` positional parameters for state filter, start date, and end date. This lets the same SQL file serve both the full-dataset run and filtered runs without string interpolation or SQL injection risk.

### Deduplication pattern
Several queries join `order_items` to `orders`. Because one order can have multiple items from multiple sellers, a naive join fans out rows and inflates counts. We handle this with a `ROW_NUMBER() OVER (PARTITION BY order_id)` CTE that collapses each order to one representative row before aggregation. This pattern is used in both `delivery_time_analysis.sql` and was the root cause of the `on_time_rate_pct > 100%` bug fixed in the final milestone.

### Composite score normalization
The seller scorecard normalizes each metric using min-max scaling before applying weights. This ensures a seller with $1M revenue and a seller with $1K revenue are compared on relative performance within the dataset rather than absolute values. The cancellation rate is inverted (`1 - normalized`) so that lower cancellation = higher score, consistent with the other three metrics.

### ABC classification
Revenue percentage and cumulative percentage are computed with window functions (`SUM() OVER (ORDER BY revenue DESC)`). Tier boundaries (80% / 95% / 100%) are applied as a `CASE` expression on the cumulative column. This is standard Pareto/ABC inventory analysis practice.

---

## Deliverable Design Decisions

### Format: Excel over Quarto and Marimo
Excel was chosen because it requires no installation, works offline, and is universally available to business stakeholders. Quarto requires a Quarto installation and R or Python. Marimo WASM export requires a modern browser and is less familiar to non-technical audiences. A `.xlsx` file can be emailed, opened in OneDrive, and explored interactively without any setup.

### One function per sheet
Each sheet in `report.py` is a self-contained function. This makes it easy to add, remove, or modify a single sheet without touching the others. The `build()` function is the only place that knows the full sheet order.

### Color system
A small palette of named constants (`_NAVY`, `_TEAL`, `_ACCENT`, `_GREEN`) is defined at the top of `report.py`. All formats reference these constants rather than hardcoded hex strings. Changing the primary color requires editing one line.

### Chart placement
Charts are inserted below their source data table on the same sheet using `ws.insert_chart(f"A{n + 5}", chart)` where `n` is the number of data rows. This keeps the data and its visualization together and ensures the chart position adjusts automatically if the dataset grows.

### Composite score color coding
Seller composite scores are colored green (≥ 0.6), orange (0.3–0.6), or red (< 0.3) directly in the cell format. This lets a manager scan thousands of rows and immediately identify problem sellers without filtering or sorting.

---

## Known Limitations

- `chart.html` requires internet access to load Vega/Vega-Lite CDN scripts; it is not self-contained
- All outputs are written to `output/` regardless of `--db-path`; there is no per-run output directory
- The pipeline does not validate that `--end-date` is after `--start-date` at argument parse time
- Successive runs overwrite previous outputs with no versioning
- The Excel report embeds charts as XlsxWriter native charts, not images; chart styling is limited to what XlsxWriter supports
