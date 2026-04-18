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
| --halt-on-validation-failure | flag | false | If set, pipeline stops on validation failure instead of continuing |

## Outputs

All outputs are written to the output/ directory. List of specific outputs below

- summary.csv -
This is a .csv file containing: seller count per state, total revenue per state, average composite score for sellers, average on-time delivery rate, average review score, global ABC product tier counts (A/B/C), and the most recent cohort retention rate (30-day).

This file should be used to evaluate and compare seller performance across states

- detail.parquet -
This is a .parquet file containing: product revenue, revenue percentage contribution, cumulative percentage, and the product's ABC classification (A/B/C tiers)

This file should be used to evaluate product performance on the market and the value of a product to sellers

- chart.html -
This is a .html, made using Vega-Altair, file containing: total revenue, with seller state on the x-axis and average composite score on the y-axis.

This file should be used as a visual reference of seller across states

## Validation Checks

List each validation check your pipeline runs before analysis and what happens if it fails.

## Analysis Summary

Brief narrative of your analytical findings (carried forward from M1, updated if needed).

## Limitations & Caveats

What the pipeline does not handle, known edge cases, etc.
