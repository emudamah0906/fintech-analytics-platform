# Snowflake Native Layer

Deployable Snowflake artifacts demonstrating native compute processing. Run the
scripts in order against a Snowflake account (SnowSQL, Snowsight worksheet, or the
VS Code extension).

| File | What it shows |
|------|---------------|
| `01_warehouse_rbac.sql` | Warehouse, databases/schemas, and **RBAC** role hierarchy (admin → analyst → viewer) mirroring the API |
| `02_raw_tables_streams.sql` | Raw landing tables + a **Stream** for change-data-capture |
| `03_dynamic_tables.sql` | **Dynamic Tables** (Silver + Gold) with declarative `TARGET_LAG` auto-refresh |
| `04_tasks.sql` | A stream-driven **Task** that processes only the delta and skips empty runs |
| `05_stored_procedures.sql` | A SQL-scripting **stored procedure** and a **Snowpark (Python)** procedure |
| `snowpark/transform.py` | Standalone **Snowpark** DataFrame transformation (RAW → curated) |

## Deploy

```bash
# example with SnowSQL
snowsql -a <account> -u <user> -f 01_warehouse_rbac.sql
snowsql -a <account> -u <user> -f 02_raw_tables_streams.sql
snowsql -a <account> -u <user> -f 03_dynamic_tables.sql
snowsql -a <account> -u <user> -f 04_tasks.sql
snowsql -a <account> -u <user> -f 05_stored_procedures.sql

# Snowpark transform (reads SNOWFLAKE_* env vars)
pip install snowflake-snowpark-python
python snowpark/transform.py
```

When the API's `SNOWFLAKE_*` env vars are set, `/api/v1/analytics/*` reports
`"source": "snowflake"`; otherwise it serves the same logic from PostgreSQL.
