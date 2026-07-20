# Procurement ETL Pipeline

Weekly procurement reporting pipeline built with **Apache Airflow**,
**Python (pandas)**, **PostgreSQL**, and **dbt**, running on
**Docker Compose**. Recreates a real-world SAP-based procurement reporting
workflow (purchase requisitions and purchase orders, weekly snapshots)
using fully synthetic data.

> **Status:** work in progress — project scaffolding.

## Planned architecture

Synthetic SAP-like extracts (xlsx) → header-based column mapping (YAML
config) → weekly snapshot transforms (composite keys, deduplication,
lookup enrichment) → staging → UPSERT into PostgreSQL → dbt models
(staging → marts) → BI dashboard (Metabase). Orchestrated by an Airflow
DAG with per-branch fail-fast dependencies, backfill support, data quality
checks, and failure alerts.

## Roadmap

1. Synthetic data generator (realistic "dirty data" archetypes)
2. ETL core as a standalone CLI (no orchestrator required)
3. Airflow DAG: schedule, sensors, backfill
4. Observability: run log, alerts, data quality checks
5. dbt: staging → marts, tests, docs
6. Object storage layer (MinIO/S3)
7. BI dashboard (Metabase)
8. CI/CD (GitHub Actions)

## Repository layout

```text
procurement-etl-airflow/
├── datagen/         # synthetic SAP-like extract generator (Stage 1)
├── etl/             # pipeline core: extract → resolve → transform → load
│   └── transform/   # one module per dataset
├── config/datasets/ # declarative column mapping (YAML) — Stage 4
├── dags/            # Airflow DAGs — Stage 3
├── dbt/             # staging → marts models — Stage 5
├── seeds/           # reference tables — Stage 5
├── sql/init/        # schema DDL: raw / staging / marts / meta
├── tests/           # pytest suite
├── checkpoints/     # `make checkpoint N` — real-system verification
├── Makefile         # developer entrypoints (`make help`)
└── pyproject.toml   # dependencies, ruff, pytest
```

Most directories are skeletons today; each is filled in by the stage noted above.

## Local development

```bash
make help          # list available commands
make checkpoint 0  # verify environment & repo skeletons
make test          # run the pytest suite
make lint          # ruff check
make fmt           # ruff format
```

Requires Python 3.12+ and Docker. From Stage 2 the pipeline also expects a local
PostgreSQL via Docker Compose. All data is synthetic — generated locally, never
committed.
