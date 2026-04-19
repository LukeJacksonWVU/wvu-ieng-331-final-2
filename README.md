# wvu-ieng-331-m2-2
WVU IENG 331 Project Milestone 2 Group 2

**Team 2**: Luke Jackson, Gavin Miller, William Muhly

## How to Run

Instructions to run the pipeline from a fresh clone:

```bash
git clone https://github.com/LukeJacksonWVU/wvu-ieng-331-m2-2.git
cd wvu-ieng-331-m2-2
uv sync
# place olist.duckdb in the data/ directory
uv run wvu-ieng-331-m2-2
uv run wvu-ieng-331-m2-2 --start-date 2026-01-01 --seller-state SP
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--start-date` | date | None (no filter) | Inclusive lower bound for date of purchase from order_purchase_timestamp |
| `--end-date` | date | None (no filter) | Inclusive upper bound for date of purchase from order_purchase_timestamp |
|`--db-path` | path | data/olist.duckdb | Path to DuckDB database file |
| `--seller-state` | string | none (no filter) | Two letter state abbreviation |
| `--halt-on-validation-failure` | flag | false | If set, pipeline stops on validation failure instead of continuing |

## Outputs

All outputs are written to the `output/` directory and created at runtime. List of specific outputs below

- `summary.csv` -
This is a .csv file containing: seller count per state, total revenue per state, average composite score for sellers, average on-time delivery rate, average review score, global ABC product tier counts (A/B/C), and the most recent cohort retention rate (30-day).

This file should be used to evaluate and compare seller performance across states

- `detail.parquet` -
This is a .parquet file containing: product revenue, revenue percentage contribution, cumulative percentage, and the product's ABC classification (A/B/C tiers)

This file should be used to evaluate product performance on the market and the value of a product to sellers

- `chart.html` -
This is a .html, made using Vega-Altair, file containing: total revenue, with seller state on the x-axis and average composite score on the y-axis.

This file should be used as a visual reference of seller performance across states

## Validation Checks

Prior to analysis, the pipeline performs the following validation checks:

- Database Validation: Ensures the DuckDB database actually exists. If not, pipeline stops with an error output.
- Schema Validation: Confirms that required tables and columns exist. If not, validation fails.
- Data Quality: Ensures that key fields, such as timestamps, are not null. Also ensures that data is logically consistent, such as end dates following start dates.

- On failure: `--halt-on-validation-failure` is set and pipeline stops

## Analysis Summary

Broadly, the pipeline analyzes seller and product performance from olist e-commerce data

Composite scorecards are made by combining revenue, on-time delivery performance, and customer reviews. 

Pareto analysis is done on products to classify products into three tiers: A,B, and C. A is the top 80% of revenue, B is the middle 15%, and C is the bottom 5%. 

Customers are grouped into cohorts by first purchase month, their repeat behavior is tracked, and their cohort's 30 day retnetion rate (whether they re-order in 30 days) is calculated.

Delivery times are evaluated to compare estimated delivery with real delivery across states (state to state shipping are called "corridors"). This lets us see which corriodors are under or over performing.


## Limitations & Caveats

chart.html requires internet access to load

The pipeline does not handle invald dates (i.e. end date before start date)

All outputs go to the `outputs/` directory, which can get confusing if multiple runs are conducted.

Any changes to DuckDB schema may cause errors in the pipeline. The pipeline is hardcoded so to speak

Large files are not optimized and performance issues will arise as files get larger
