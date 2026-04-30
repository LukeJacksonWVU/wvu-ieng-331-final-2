# wvu-ieng-331-final-2

WVU IENG 331 — Final Data Product, **Team 2**

**Team Members:** Luke Jackson, Gavin Miller, William Muhly

---

## How to Run

```bash
git clone https://github.com/LukeJacksonWVU/wvu-ieng-331-final-2.git
cd wvu-ieng-331-final-2
uv sync
# place olist.duckdb in the data/ directory
uv run wvu-ieng-331-final-2
```

Optional filters:

```bash
uv run wvu-ieng-331-final-2 --start-date 2017-01-01 --end-date 2018-12-31
uv run wvu-ieng-331-final-2 --seller-state SP
uv run wvu-ieng-331-final-2 --db-path /path/to/olist.duckdb --halt-on-validation-failure
```

---

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--db-path` | path | `data/olist.duckdb` | Path to DuckDB database file |
| `--start-date` | YYYY-MM-DD | None | Inclusive lower bound on order purchase date |
| `--end-date` | YYYY-MM-DD | None | Inclusive upper bound on order purchase date |
| `--seller-state` | XX | None | Two-letter Brazilian state abbreviation filter |
| `--halt-on-validation-failure` | flag | false | Stop pipeline on validation failure instead of warning |

---

## Outputs

All outputs are written to the `output/` directory (created at runtime, gitignored).

| File | Description |
|---|---|
| `summary.csv` | State-level aggregation: seller count, total revenue, avg composite score, avg on-time rate, avg review score, ABC tier counts, latest cohort retention |
| `detail.parquet` | Product-level ABC classification: revenue, revenue %, cumulative %, tier (A/B/C) |
| `chart.html` | Altair interactive bar chart — avg composite score by seller state (requires internet for CDN) |
| `report.xlsx` | **Final deliverable** — polished Excel workbook for non-technical stakeholders |

---

## Final Deliverable

### Format: Excel Workbook (`report.xlsx`)

We chose Excel because it requires no installation beyond software already on every business computer. A manager can open `report.xlsx` directly from email or OneDrive with zero setup. The single-file format also makes it easy to share.

### Workbook Structure

| Sheet | Purpose |
|---|---|
| **Cover** | Executive summary with 6 KPI tiles, ABC tier summary, best delivery corridor, and a 5-point analytical narrative with business recommendations |
| **Seller Scorecard** | Full ranked seller table (3,095 rows) with composite score color-coded green/orange/red. Freeze panes for easy scrolling. |
| **Chart – Seller Score by State** | Figure 1 — horizontal bar chart of avg composite score for the top 15 states |
| **Cohort Retention** | Monthly cohort table with 30/60/90-day retention rates and Figure 2 line chart |
| **ABC Analysis** | Full product ABC classification table and Figure 3 column chart of revenue by tier |
| **Delivery Analysis** | All 412 corridors ranked by on-time rate and Figure 4 bar chart of top 20 corridors |

### Visualizations

1. **Figure 1 — Seller Composite Score by State** *(categorical comparison)*
   Bar chart ranking the top 15 Brazilian states by average composite seller score. Reveals quality differences that raw revenue totals hide — some smaller states outperform São Paulo on a per-seller basis.

2. **Figure 2 — Cohort Retention Rates Over Time** *(change over time)*
   Line chart with three series (30-day, 60-day, 90-day retention) plotted across monthly cohorts from 2016 to 2018. Shows that repeat-purchase rate is structurally low across all cohorts, with mid-2017 cohorts showing the highest early re-engagement.

3. **Figure 3 — Revenue by ABC Product Tier** *(categorical comparison)*
   Column chart showing total revenue by Tier A, B, and C. Visualizes the Pareto concentration — Tier A products dominate revenue despite representing a small fraction of the catalog.

4. **Figure 4 — Top 20 Delivery Corridors by On-Time Rate** *(categorical comparison)*
   Horizontal bar chart of the 20 best-performing seller-to-customer state corridors. Used alongside the full corridor table to identify where logistics investment would have the highest impact.

### How to Open

Double-click `output/report.xlsx` in Finder or Windows Explorer. No installation required beyond Microsoft Excel.

---

## Validation Checks

Run automatically before every analysis:

- **Database validation** — confirms `olist.duckdb` exists at the specified path
- **Schema validation** — verifies all required tables and columns are present
- **Data quality** — checks for nulls in key timestamp fields and logical date ordering

On failure: logs a warning and continues by default. Pass `--halt-on-validation-failure` to stop instead.

---

## Analysis Summary

The pipeline analyzes seller and product performance across Olist's Brazilian e-commerce marketplace across four dimensions:

**Seller Scorecard** — Composite performance score combining revenue (30%), on-time delivery (30%), customer reviews (25%), and low cancellation rate (15%). Each metric is min-max normalized before weighting so sellers of different sizes are fairly compared.

**ABC Product Classification** — Pareto analysis classifying every product into Tier A (top 80% of revenue), Tier B (next 15%), or Tier C (bottom 5%). Helps prioritize inventory and marketing decisions.

**Cohort Retention** — Customers are grouped by their first-purchase month. The pipeline tracks what fraction re-order within 30, 60, and 90 days, revealing structural patterns in customer loyalty.

**Delivery Corridor Analysis** — Compares estimated vs. actual delivery times on every seller-state to customer-state corridor, computing on-time rate and average days early or late.

---

## Bug Fixes (Final vs M2)

- **seller_scorecard.sql** — Fixed `on_time_rate_pct` exceeding 100% by replacing `SUM(CASE WHEN ... THEN 1)` with `COUNT(DISTINCT CASE WHEN ... THEN order_id)` in the `seller_delivery` CTE. The original counted item rows in the numerator but distinct orders in the denominator.
- **delivery_time_analysis.sql** — Fixed corridor on-time rates exceeding 100% by deduplicating the `order_items` join using a `ROW_NUMBER()` CTE before computing corridor metrics.

---

## Limitations

- `chart.html` requires internet access to load Vega/Vega-Lite CDN scripts
- All outputs go to `output/` regardless of the `--db-path` used; successive runs overwrite previous outputs
- Schema changes in the DuckDB file may cause query failures; the pipeline is built for the Olist public dataset schema
