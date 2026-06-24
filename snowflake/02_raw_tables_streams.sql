-- =============================================================================
-- 02 | Raw landing tables + Streams for change-data-capture
-- =============================================================================
USE DATABASE FINSTREAM;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS RAW.TRANSACTIONS (
    id            NUMBER AUTOINCREMENT,
    merchant_id   NUMBER         NOT NULL,
    amount        NUMBER(14,2)   NOT NULL,
    currency      STRING         DEFAULT 'USD',
    status        STRING         DEFAULT 'settled',
    card_type     STRING         DEFAULT 'credit',
    created_at    TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at    TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS RAW.MERCHANTS (
    id        NUMBER AUTOINCREMENT,
    name      STRING NOT NULL,
    country   STRING NOT NULL,
    mcc       STRING NOT NULL
);

-- Stream captures inserts/updates/deletes on the raw feed so downstream
-- tasks process only the delta (incremental, not full re-scan).
CREATE STREAM IF NOT EXISTS RAW.TRANSACTIONS_STREAM
  ON TABLE RAW.TRANSACTIONS
  SHOW_INITIAL_ROWS = TRUE;
