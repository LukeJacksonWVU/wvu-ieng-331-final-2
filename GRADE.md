# Final Deliverable Grade

**Team 2 (Luke Jackson, Gavin Miller, William)**

| Criterion | Score | Max |
|-----------|------:|----:|
| Deliverable Quality | 6 | 6 |
| Visualizations | 6 | 6 |
| Pipeline Integration | 6 | 6 |
| Analytical Narrative | 6 | 6 |
| **Total (rubric portion)** | **24** | **24** |

Video walkthrough graded separately.

## Deliverable Quality (6/6)

`output/report.xlsx` is a six-sheet Excel workbook (Cover, Seller Scorecard, Chart - Seller Score by State, Cohort Retention, ABC Analysis, Delivery Analysis). The cover sheet has KPI tiles plus a five-point analytical narrative. The Seller Scorecard sheet uses colour-coded composite scores (green/orange/red) and freeze panes for navigation. Each chart lives on its own sheet alongside the supporting data table. Native Excel format means a manager can open it from email or OneDrive with no setup. The polish and organisation are appropriate for a business audience.

## Visualizations (6/6)

Four visualisations, exceeding the three-chart minimum and covering all required types:

- **Figure 1: Seller Composite Score by State** (categorical bar) - top 15 states ranked by per-seller composite score.
- **Figure 2: Cohort Retention Rates Over Time** (temporal line) - 30/60/90-day retention plotted across monthly cohorts.
- **Figure 3: Revenue by ABC Product Tier** (categorical column) - Pareto concentration visualised.
- **Figure 4: Top 20 Delivery Corridors by On-Time Rate** (categorical bar) - best-performing seller-customer state pairs.

Captions in the README explain what each chart shows and what insight it surfaces. Chart types match the data well (line for time series, bar for categories).

## Pipeline Integration (6/6)

`uv run wvu-ieng-331-final-2` after `uv sync` runs the full pipeline: validation, queries (5 SQL files: scorecard, ABC, cohort, delivery, plus several validation SQL), aggregation, and Excel report build. Tested with the extended database; pipeline ran end-to-end without errors and produced report.xlsx (1.9 MB). The five-step orchestration is logged clearly via loguru.

## Analytical Narrative (6/6)

Cover sheet has KPI tiles, an ABC tier summary, the best-performing delivery corridor, and a five-point analytical narrative with business recommendations. The composite seller score is documented (30% revenue, 30% on-time delivery, 25% reviews, 15% low cancellation, all min-max normalised so different-sized sellers can be compared fairly), which shows real analytical thought. README has a separate "Bug Fixes (Final vs M2)" section showing iterative improvement from M2 (corrected a bug where `on_time_rate_pct` exceeded 100% due to mismatched COUNT vs COUNT DISTINCT in seller scorecard, deduplicated order_items in delivery corridor analysis). This kind of evidence is what distinguishes a polished deliverable from a thin one.
