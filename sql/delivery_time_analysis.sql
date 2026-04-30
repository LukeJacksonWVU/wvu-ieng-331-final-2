-- Parameters:
--   $1 :: VARCHAR  -- seller_state filter (NULL = all states)
--   $2 :: DATE     -- start_date filter   (NULL = no lower bound)
--   $3 :: DATE     -- end_date filter     (NULL = no upper bound)

WITH order_seller AS (
    SELECT order_id, seller_state
        FROM (
            SELECT
                oi.order_id,
                s.seller_state,
                ROW_NUMBER() OVER (PARTITION BY oi.order_id ORDER BY s.seller_state) AS rn
            FROM order_items oi
            JOIN sellers s ON oi.seller_id = s.seller_id
            WHERE ($1 IS NULL OR s.seller_state = $1)
        )
        WHERE rn = 1
),
delivery_times AS (
    SELECT
        o.order_id,
        c.customer_state,
        os.seller_state,
        datediff('day', o.order_purchase_timestamp, o.order_delivered_customer_date)      AS actual_days,
        datediff('day', o.order_purchase_timestamp, o.order_estimated_delivery_date)      AS estimated_days,
        datediff('day', o.order_delivered_customer_date, o.order_estimated_delivery_date) AS days_early_late
    FROM orders o
    JOIN customers    c  ON o.customer_id = c.customer_id
    JOIN order_seller os ON o.order_id    = os.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
      AND ($2 IS NULL OR CAST(o.order_purchase_timestamp AS DATE) >= $2)
      AND ($3 IS NULL OR CAST(o.order_purchase_timestamp AS DATE) <= $3)
),
corridor_metrics AS (
    SELECT
        seller_state,
        customer_state,
        seller_state || ' → ' || customer_state AS corridor,
        COUNT(*)                                 AS total_deliveries,
        ROUND(AVG(actual_days),      1)          AS avg_actual_days,
        ROUND(AVG(estimated_days),   1)          AS avg_estimated_days,
        ROUND(AVG(days_early_late),  1)          AS avg_days_early_late,
        SUM(CASE WHEN days_early_late >= 0 THEN 1 ELSE 0 END) AS on_time_count,
        SUM(CASE WHEN days_early_late <  0 THEN 1 ELSE 0 END) AS late_count
    FROM delivery_times
    GROUP BY seller_state, customer_state
),
corridor_rates AS (
    SELECT
        corridor, seller_state, customer_state,
        total_deliveries, avg_actual_days, avg_estimated_days, avg_days_early_late,
        ROUND(on_time_count * 100.0 / total_deliveries, 2) AS on_time_rate_pct,
        ROUND(late_count    * 100.0 / total_deliveries, 2) AS late_rate_pct,
        RANK() OVER (ORDER BY avg_days_early_late DESC) AS rank_best_corridors,
        RANK() OVER (ORDER BY avg_days_early_late ASC)  AS rank_worst_corridors
    FROM corridor_metrics
)
SELECT
    corridor, total_deliveries,
    avg_actual_days, avg_estimated_days, avg_days_early_late,
    on_time_rate_pct, late_rate_pct,
    rank_best_corridors, rank_worst_corridors
FROM corridor_rates
ORDER BY avg_days_early_late DESC;
