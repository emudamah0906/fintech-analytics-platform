# FinStream — Fintech Analytics Platform

A **financial-analytics API** for payments data: a FastAPI microservice backed by
**PostgreSQL + Snowflake**, with JWT/OAuth2 authentication, role-based access
control, Docker, and CI. It ingests transaction and merchant data and serves
governed analytical endpoints over both an OLTP store and Snowflake-native compute.

---

## Architecture

```
                         ┌──────────────────────────────┐
   client ──HTTPS──▶     │  FastAPI  (app/)              │
   (JWT bearer)          │  • OAuth2 + JWT auth          │
                         │  • RBAC: admin/analyst/viewer │
                         │  • /api/v1 versioned, OpenAPI │
                         │  • request-id + security hdrs │
                         └───────┬───────────────┬──────┘
                                 │               │
                  async SQLAlchemy 2.0      Snowflake connector
                                 │               │ (when configured)
                         ┌───────▼──────┐  ┌─────▼───────────────────────┐
                         │ PostgreSQL   │  │ Snowflake native compute    │
                         │ (app + OLAP) │  │ Snowpark · Streams · Tasks  │
                         │ tuned SQL    │  │ Dynamic Tables · Stored Proc│
                         └──────────────┘  └─────────────────────────────┘
```

The same analytical logic runs on **PostgreSQL** by default and **offloads to
Snowflake** when credentials are configured (the `/analytics` responses report
which engine served them).

---

## Features

| Area | Details |
|------|---------|
| **API** | FastAPI (async) + Pydantic, versioned `/api/v1`, OpenAPI/Swagger at `/docs` |
| **Snowflake** | Snowpark (Python), stored procedures, tasks, streams, dynamic tables (`snowflake/`) |
| **SQL** | Tuned analytical queries across Snowflake + PostgreSQL (`sql/postgres/`) |
| **Security** | JWT/OAuth2 auth, RBAC, OWASP hardening (headers, bcrypt, parameterized queries) |
| **Observability** | Request-id propagation, request timing, structured JSON logging |
| **Delivery** | Docker + docker-compose, GitHub Actions CI (ruff + pytest + image build) |

---

## Quick start

### Option A — Docker (API + PostgreSQL)

```bash
cp .env.example .env
docker compose up --build
# API:    http://localhost:8000
# Swagger http://localhost:8000/docs
```

### Option B — local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.db.seed        # creates tables + sample data (SQLite/Postgres)
uvicorn app.main:app --reload
```

### Try it

```bash
# 1) get a token (seeded users: admin@finstream.dev / analyst@finstream.dev / viewer@finstream.dev)
curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=analyst@finstream.dev&password=analyst12345" | jq -r .access_token

# 2) call an analytics endpoint
curl -s http://localhost:8000/api/v1/analytics/summary \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Security notes (OWASP Top 10)

- **A01 Broken Access Control** — RBAC enforced via FastAPI dependencies (`require_role`).
- **A02 Cryptographic Failures** — bcrypt password hashing; JWTs signed and expiring.
- **A03 Injection** — SQLAlchemy ORM / parameterized queries; Pydantic validates all input.
- **A05 Security Misconfiguration** — restrictive CORS, hardening response headers, non-root container.
- **A07 Auth Failures** — uniform login errors, short-lived tokens, `WWW-Authenticate` challenge.

---

## Tests

```bash
pytest -q          # auth, RBAC, and analytics covered (SQLite in-memory)
ruff check .       # lint
```

## API surface (v1)

| Method | Path | Min role | Purpose |
|--------|------|----------|---------|
| POST | `/api/v1/auth/token` | — | OAuth2 login → JWT |
| GET  | `/api/v1/auth/me` | any | current user |
| POST | `/api/v1/auth/users` | admin | create user |
| GET  | `/api/v1/transactions` | viewer | list (paginated, filterable) |
| POST | `/api/v1/transactions` | analyst | ingest a transaction |
| GET  | `/api/v1/analytics/summary` | viewer | portfolio KPIs |
| GET  | `/api/v1/analytics/top-merchants` | viewer | volume leaderboard |
| GET  | `/health` | — | liveness probe |
