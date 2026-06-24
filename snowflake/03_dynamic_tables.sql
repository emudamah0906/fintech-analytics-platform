-- =============================================================================
-- 03 | Dynamic Tables — declarative, auto-refreshing analytical models
-- Snowflake manages the incremental refresh to meet the TARGET_LAG.
-- =============================================================================
USE DATABASE FINSTREAM;
USE SCHEMA ANALYTICS;

-- Cleaned, conformed transaction layer (Silver).
CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.DT_TRANSACTIONS_CLEAN
  TARGET_LAG = '5 minutes'
  WAREHOUSE = FINSTREAM_WH
AS
SELECT
    id,
    merchant_id,
    amount,
    UPPER(currency)                          AS currency,
    LOWER(status)                            AS status,
    LOWER(card_type)                         AS card_type,
    created_at,
    DATE_TRUNC('day', created_at)            AS txn_date
FROM FINSTREAM.RAW.TRANSACTIONS
WHERE amount > 0;

-- Daily merchant aggregate (Gold) — powers the /analytics endpoints.
CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.DT_MERCHANT_DAILY
  TARGET_LAG = '5 minutes'
  WAREHOUSE = FINSTREAM_WH
AS
SELECT
    t.merchant_id,
    m.name                                                   AS merchant_name,
    t.txn_date,
    COUNT(*)                                                 AS transaction_count,
    SUM(t.amount)                                            AS total_volume,
    AVG(t.amount)                                            AS avg_ticket,
    SUM(IFF(t.status = 'settled', 1, 0)) / COUNT(*)          AS approval_rate
FROM ANALYTICS.DT_TRANSACTIONS_CLEAN t
JOIN FINSTREAM.RAW.MERCHANTS m ON m.id = t.merchant_id
GROUP BY t.merchant_id, m.name, t.txn_date;
