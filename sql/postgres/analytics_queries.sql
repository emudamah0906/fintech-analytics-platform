-- =============================================================================
-- PostgreSQL analytical queries + the indexes that make them fast.
-- These mirror the logic the API runs via SQLAlchemy, written as tuned SQL.
-- =============================================================================

-- Supporting indexes (also declared on the ORM model):
--   composite index drives the time-window + merchant grouping access path.
CREATE INDEX IF NOT EXISTS ix_txn_created_merchant ON transactions (created_at, merchant_id);
CREATE INDEX IF NOT EXISTS ix_txn_status           ON transactions (status);

-- 1) Portfolio KPI summary (single pass).
SELECT
    COALESCE(SUM(amount), 0)                                       AS total_volume,
    COUNT(*)                                                       AS transaction_count,
    ROUND(AVG(amount), 2)                                          AS avg_ticket,
    ROUND(SUM(CASE WHEN status = 'settled' THEN 1 ELSE 0 END)::numeric
          / NULLIF(COUNT(*), 0), 4)                                AS approval_rate
FROM transactions;

-- 2) Top merchants by volume (uses the join + grouping index path).
SELECT
    m.id                       AS merchant_id,
    m.name                     AS merchant_name,
    SUM(t.amount)              AS total_volume,
    COUNT(*)                   AS transaction_count
FROM transactions t
JOIN merchants m ON m.id = t.merchant_id
GROUP BY m.id, m.name
ORDER BY total_volume DESC
LIMIT 10;

-- 3) Daily volume trend with a 7-row moving average (window function).
SELECT
    day,
    daily_volume,
    ROUND(AVG(daily_volume) OVER (
        ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2)                       AS volume_ma_7d
FROM (
    SELECT date_trunc('day', created_at) AS day, SUM(amount) AS daily_volume
    FROM transactions
    GROUP BY 1
) d
ORDER BY day;

-- Inspect the plan to confirm index usage instead of a seq scan:
-- EXPLAIN ANALYZE SELECT ... ;
