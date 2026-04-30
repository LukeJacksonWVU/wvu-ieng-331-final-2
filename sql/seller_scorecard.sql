-- Parameters:
--   $1 :: VARCHAR  -- seller_state filter  (NULL = all states)
--   $2 :: DATE     -- start_date filter    (NULL = no lower bound)
--   $3 :: DATE     -- end_date filter      (NULL = no upper bound)

WITH seller_revenue AS (
    SELECT
        oi.seller_id,
        COUNT(DISTINCT oi.order_id)                AS total_orders,
        ROUND(SUM(oi.price + oi.freight_value), 2) AS total_revenue
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
      AND ($2 IS NULL OR CAST(o.order_purchase_timestamp AS DATE) >= $2)
      AND ($3 IS NULL OR CAST(o.order_purchase_timestamp AS DATE) <= $3)
    GROUP BY oi.seller_id
),

seller_delivery AS (
    SELECT
        oi.seller_id,
        ROUND(
            COUNT(DISTINCT CASE
                WHEN CAST(o.order_delivered_customer_date AS DATE)
                     <= CAST(o.order_estimated_delivery_date AS DATE)
                THEN o.order_id ELSE NULL
            END) * 100.0 / COUNT(DISTINCT o.order_id),
        2) AS on_time_rate_pct
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
      AND ($2 IS NULL OR CAST(o.order_purchase_timestamp AS DATE) >= $2)
      AND ($3 IS NULL OR CAST(o.order_purchase_timestamp AS DATE) <= $3)
    GROUP BY oi.seller_id
),

seller_reviews AS (
    SELECT
        oi_dedup.seller_id,
        ROUND(AVG(r.review_score), 2) AS avg_review_score
    FROM (SELECT DISTINCT seller_id, order_id FROM order_items) oi_dedup
    JOIN order_reviews r ON oi_dedup.order_id = r.order_id
    GROUP BY oi_dedup.seller_id
),
seller_cancellations AS (
    SELECT
        oi.seller_id,
        ROUND(
            SUM(CASE WHEN o.order_status IN ('canceled', 'unavailable') THEN 1 ELSE 0 END)
            * 100.0 / COUNT(DISTINCT o.order_id),
        2) AS cancellation_rate_pct
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
      AND ($2 IS NULL OR CAST(o.order_purchase_timestamp AS DATE) >= $2)
      AND ($3 IS NULL OR CAST(o.order_purchase_timestamp AS DATE) <= $3)
    GROUP BY oi.seller_id
),
combined_metrics AS (
    SELECT
        s.seller_id,
        s.seller_city,
        s.seller_state,
        COALESCE(sr.total_orders,          0) AS total_orders,
        COALESCE(sr.total_revenue,         0) AS total_revenue,
        COALESCE(sd.on_time_rate_pct,      0) AS on_time_rate,
        COALESCE(sv.avg_review_score,      0) AS avg_review_score,
        COALESCE(sc.cancellation_rate_pct, 0) AS cancellation_rate
    FROM sellers s
    LEFT JOIN seller_revenue       sr ON s.seller_id = sr.seller_id
    LEFT JOIN seller_delivery      sd ON s.seller_id = sd.seller_id
    LEFT JOIN seller_reviews       sv ON s.seller_id = sv.seller_id
    LEFT JOIN seller_cancellations sc ON s.seller_id = sc.seller_id
    WHERE ($1 IS NULL OR s.seller_state = $1)
),
normalized AS (
    SELECT
        seller_id, seller_city, seller_state,
        total_orders, total_revenue, on_time_rate, avg_review_score, cancellation_rate,
        (total_revenue - MIN(total_revenue) OVER ())
            / NULLIF(MAX(total_revenue) OVER () - MIN(total_revenue) OVER (), 0) AS norm_revenue,
        (on_time_rate - MIN(on_time_rate) OVER ())
            / NULLIF(MAX(on_time_rate) OVER () - MIN(on_time_rate) OVER (), 0)  AS norm_on_time,
        (avg_review_score - MIN(avg_review_score) OVER ())
            / NULLIF(MAX(avg_review_score) OVER () - MIN(avg_review_score) OVER (), 0) AS norm_review,
        1 - (cancellation_rate - MIN(cancellation_rate) OVER ())
            / NULLIF(MAX(cancellation_rate) OVER () - MIN(cancellation_rate) OVER (), 0) AS norm_cancellation
    FROM combined_metrics
)
SELECT
    seller_id, seller_city, seller_state,
    total_orders, total_revenue,
    on_time_rate      AS on_time_rate_pct,
    avg_review_score,
    cancellation_rate AS cancellation_rate_pct,
    ROUND(
        (COALESCE(norm_revenue,      0) * 0.30) +
        (COALESCE(norm_on_time,      0) * 0.30) +
        (COALESCE(norm_review,       0) * 0.25) +
        (COALESCE(norm_cancellation, 0) * 0.15),
    4) AS composite_score,
    DENSE_RANK() OVER (
        ORDER BY
            (COALESCE(norm_revenue,      0) * 0.30) +
            (COALESCE(norm_on_time,      0) * 0.30) +
            (COALESCE(norm_review,       0) * 0.25) +
            (COALESCE(norm_cancellation, 0) * 0.15)
        DESC
    ) AS seller_rank
FROM normalized
ORDER BY seller_rank ASC;
