-- =============================================================================
-- 04 | Tasks — scheduled, stream-driven processing
-- =============================================================================
USE DATABASE FINSTREAM;
USE SCHEMA ANALYTICS;

-- A fraud-flag table populated incrementally from the stream.
CREATE TABLE IF NOT EXISTS ANALYTICS.HIGH_VALUE_ALERTS (
    transaction_id NUMBER,
    merchant_id    NUMBER,
    amount         NUMBER(14,2),
    flagged_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Task runs only when the stream has new data (SYSTEM$STREAM_HAS_DATA),
-- avoiding wasted warehouse credits on empty runs.
CREATE OR REPLACE TASK ANALYTICS.FLAG_HIGH_VALUE_TXNS
  WAREHOUSE = FINSTREAM_WH
  SCHEDULE = '1 minute'
  WHEN SYSTEM$STREAM_HAS_DATA('FINSTREAM.RAW.TRANSACTIONS_STREAM')
AS
INSERT INTO ANALYTICS.HIGH_VALUE_ALERTS (transaction_id, merchant_id, amount)
SELECT id, merchant_id, amount
FROM FINSTREAM.RAW.TRANSACTIONS_STREAM
WHERE METADATA$ACTION = 'INSERT'
  AND amount >= 5000;

-- Tasks are created suspended; resume to activate.
ALTER TASK ANALYTICS.FLAG_HIGH_VALUE_TXNS RESUME;
