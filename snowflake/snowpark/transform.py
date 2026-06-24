"""Snowpark (Python) transformation job — RAW -> ANALYTICS curated layer.

Runs against Snowflake native compute. Deploy as a stored procedure or run
ad hoc:  python snowflake/snowpark/transform.py

Connection is read from the same SNOWFLAKE_* env vars as the API (app.core.config).
"""
from __future__ import annotations

import os

from snowflake.snowpark import Session
from snowflake.snowpark.functions import avg, col, count, iff, lit
from snowflake.snowpark.functions import sum as sf_sum


def build_session() -> Session:
    cfg = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "password": os.environ["SNOWFLAKE_PASSWORD"],
        "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", "FINSTREAM_WH"),
        "database": os.environ.get("SNOWFLAKE_DATABASE", "FINSTREAM"),
        "schema": os.environ.get("SNOWFLAKE_SCHEMA", "ANALYTICS"),
        "role": os.environ.get("SNOWFLAKE_ROLE", "FINSTREAM_ANALYST"),
    }
    return Session.builder.configs(cfg).create()


def build_merchant_daily(session: Session) -> None:
    """Materialize the Gold merchant-daily aggregate using the DataFrame API."""
    txns = session.table("FINSTREAM.RAW.TRANSACTIONS").filter(col("AMOUNT") > 0)
    merchants = session.table("FINSTREAM.RAW.MERCHANTS")

    daily = (
        txns.join(merchants, txns["MERCHANT_ID"] == merchants["ID"])
        .group_by(txns["MERCHANT_ID"], merchants["NAME"])
        .agg(
            count(lit(1)).alias("TRANSACTION_COUNT"),
            sf_sum(col("AMOUNT")).alias("TOTAL_VOLUME"),
            avg(col("AMOUNT")).alias("AVG_TICKET"),
            (sf_sum(iff(col("STATUS") == "settled", 1, 0)) / count(lit(1))).alias("APPROVAL_RATE"),
        )
    )
    daily.write.mode("overwrite").save_as_table("FINSTREAM.ANALYTICS.MERCHANT_DAILY_SNOWPARK")
    print(f"Wrote {daily.count()} merchant rows to ANALYTICS.MERCHANT_DAILY_SNOWPARK")


if __name__ == "__main__":
    with build_session() as session:
        build_merchant_daily(session)
