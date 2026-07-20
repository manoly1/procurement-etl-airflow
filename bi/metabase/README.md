# Metabase — the BI layer

Metabase sits on top of the **dbt marts** (`marts.mart_open_po_weekly`,
`marts.mart_top_suppliers`) and turns them into a dashboard. It is the open-stack
replacement for Power BI: the same weekly KPIs and supplier ranking, but the
metric logic lives in versioned SQL models — not in per-report DAX measures.

## Start it

Metabase comes up with the rest of the stack:

```bash
make up          # postgres + minio + airflow + metabase (:3000)
```

Open <http://localhost:3000> and complete the one-time setup wizard.

## Connect to the warehouse

Add a database connection (Admin → Databases → Add):

| Field | Value |
|-------|-------|
| Type | PostgreSQL |
| Host | `postgres` (inside Docker) / `localhost` (from host) |
| Port | `5432` |
| Database name | `procurement` |
| Username / Password | `etl` / `etl` |
| Schemas | `marts` (the dbt marts) |

## Build the dashboard

Each file in `queries/` is the native SQL for one dashboard card. In Metabase:
**+ New → SQL query**, paste the file, run it, pick the visualization, then
**Save** and **Add to dashboard**.

| Query | Card | Visualization |
|-------|------|---------------|
| `weekly_open_value.sql` | Open PO value by week | line / bar |
| `weekly_line_count.sql` | Open PO line count by week | bar |
| `top_suppliers_latest.sql` | Top 10 suppliers, latest week | row |
| `kpi_latest_week.sql` | Latest-week KPIs | number(s) |

The queries reference only the `marts` schema, so they work as soon as
`make dbt` has built the marts. Nothing is hardcoded to a specific week — the
"latest week" cards use `max(report_week)` and follow new loads automatically.

## Why SQL files in git

Metabase questions live in its own app database, which is not version-controlled.
Keeping the card SQL here means the analytical logic is reviewable, diffable and
reproducible — a new environment rebuilds the same dashboard from these files.
