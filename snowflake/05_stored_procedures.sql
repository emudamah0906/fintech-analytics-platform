-- =============================================================================
-- 05 | Stored procedures — SQL scripting + Snowpark (Python) handler
-- =============================================================================
USE DATABASE FINSTREAM;
USE SCHEMA ANALYTICS;

-- (a) SQL-scripting procedure: refresh + return a portfolio KPI row.
CREATE OR REPLACE PROCEDURE ANALYTICS.SP_PORTFOLIO_SUMMARY()
  RETURNS TABLE (total_volume NUMBER, transaction_count NUMBER, approval_rate FLOAT)
  LANGUAGE SQL
AS
$$
DECLARE
  res RESULTSET;
BEGIN
  res := (
    SELECT
        SUM(amount)                                  AS total_volume,
        COUNT(*)                                     AS transaction_count,
        SUM(IFF(status = 'settled', 1, 0)) / COUNT(*) AS approval_rate
    FROM ANALYTICS.DT_TRANSACTIONS_CLEAN
  );
  RETURN TABLE(res);
END;
$$;

-- (b) Snowpark Python procedure: compute per-merchant z-scores for anomaly
--     detection entirely in Snowflake's native compute (no data egress).
CREATE OR REPLACE PROCEDURE ANALYTICS.SP_MERCHANT_ANOMALIES(lookback_days INT)
  RETURNS TABLE (merchant_id NUMBER, z_score FLOAT)
  LANGUAGE PYTHON
  RUNTIME_VERSION = '3.11'
  PACKAGES = ('snowflake-snowpark-python')
  HANDLER = 'run'
AS
$$
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, avg, stddev, abs as sf_abs

def run(session: Session, lookback_days: int):
    df = session.table("FINSTREAM.ANALYTICS.DT_MERCHANT_DAILY")
    stats = df.agg(
        avg(col("TOTAL_VOLUME")).alias("MU"),
        stddev(col("TOTAL_VOLUME")).alias("SIGMA"),
    ).collect()[0]
    mu, sigma = stats["MU"], (stats["SIGMA"] or 1)
    result = (
        df.group_by("MERCHANT_ID")
          .agg(avg(col("TOTAL_VOLUME")).alias("V"))
          .select(
              col("MERCHANT_ID"),
              (sf_abs(col("V") - mu) / sigma).alias("Z_SCORE"),
          )
    )
    return result
$$;
