# Procurement ETL Pipeline

[![CI](https://github.com/manoly1/procurement-etl-airflow/actions/workflows/ci.yml/badge.svg)](https://github.com/manoly1/procurement-etl-airflow/actions/workflows/ci.yml)

A weekly procurement-reporting data pipeline on a modern stack: **Apache
Airflow**, **Python (pandas)**, **PostgreSQL**, **dbt**, **MinIO** and
**Metabase**, wired together with **Docker Compose**. It reproduces a
real-world SAP-based reporting workflow — purchase requisitions and purchase
orders, captured as weekly snapshots — on **fully synthetic data** generated
locally.

The project is a portfolio rebuild of a working Excel/VBA + SQL Server + Power BI
process (orchestrated by Power Automate) onto reproducible, tested, version-
controlled data engineering tooling.

## Architecture

```mermaid
flowchart LR
    subgraph gen[Synthetic source]
      D[datagen<br/>SAP-like xlsx]
    end
    subgraph lake[Raw layer]
      M[(MinIO<br/>object store)]
    end
    subgraph core[ETL core - Python]
      E[extract<br/>header detect] --> R[resolve<br/>YAML columns]
      R --> T[transform<br/>keys, dedup, rates]
      T --> L[load<br/>UPSERT]
    end
    subgraph wh[(PostgreSQL)]
      RAW[raw] --> STG[staging] --> MRT[marts]
    end
    D --> M --> E
    L --> RAW
    STG -. dbt .-> MRT
    MRT --> BI[Metabase<br/>dashboard]
    A[Airflow DAG<br/>schedule / sensors / backfill] -.orchestrates.-> core
```

**Flow:** synthetic SAP-like extracts land in MinIO (immutable raw), the Python
core resolves columns from YAML config and builds a clean weekly snapshot
(composite keys, deduplication, FX enrichment), loads it into Postgres with an
idempotent UPSERT, dbt models it `staging → marts`, and Metabase reads the marts.
An Airflow DAG orchestrates the whole chain with per-branch fail-fast
dependencies, file sensors, retries, backfill and failure alerts. Data-quality
checks and a stage log (`meta.etl_log`) guard each run.

## Stack

| Layer | Tool | Why |
|-------|------|-----|
| Orchestration | Airflow (LocalExecutor) | schedule, sensors, backfill, retries |
| Transform (code) | Python + pandas | extract / resolve / transform / load |
| Raw storage | MinIO (S3 API) | immutable weekly extracts, cloud-portable |
| Warehouse | PostgreSQL | raw / staging / marts / meta schemas |
| Transform (SQL) | dbt | staging → marts, tests, lineage |
| BI | Metabase | dashboards over the marts |
| Quality / tests | pytest, ruff, dbt tests | code + data contracts |
| CI | GitHub Actions | lint, format, tests, dbt parse, DAG compile |

## Quickstart

```bash
# 1. Install the pipeline (Python 3.12+)
pip install -e ".[dev,dbt]"

# 2. Bring up the stack (Postgres, MinIO, Airflow, Metabase)
make up

# 3. Generate + load a week, land raw into the lake, build the marts
make etl  DATASET=open_po WEEK=29
make land DATASET=open_po WEEK=29
make dbt

# 4. Explore
#   Airflow   http://localhost:8080   (admin / admin)
#   MinIO     http://localhost:9001   (minioadmin / minioadmin)
#   Metabase  http://localhost:3000
```

`make help` lists every target. All secrets come from the environment
(`.env`, gitignored) — copy `.env.example` to start. No real data, paths or
credentials are ever committed.

## Repository layout

```text
procurement-etl-airflow/
├── datagen/          # synthetic SAP-like extract generator + dirty-data archetypes
├── etl/              # pipeline core: extract → resolve → transform → load
│   ├── transform/    # weekly-snapshot business logic
│   └── storage.py    # MinIO / S3 object store (raw layer)
├── config/datasets/  # declarative column mapping (YAML)
├── dags/             # Airflow DAG: schedule, sensors, land, snapshot, load
├── dbt/              # staging → marts models, sources, seeds, tests
├── bi/metabase/      # dashboard card SQL over the marts
├── sql/init/         # schema DDL: raw / staging / marts / meta
├── tests/            # pytest suite (unit + dirty-data fixtures + BI/SQL)
├── checkpoints/      # `make checkpoint N` — per-stage verification
├── .github/          # CI workflow + PR template
├── docker-compose.yml
├── Makefile
└── pyproject.toml
```

## Verification

Every stage ships a checkpoint that prints `STATUS: PASSED` / `FAILED`:

```bash
make checkpoint 0    # environment & skeleton
make checkpoint 9    # tests & data quality
make checkpoint 13   # CI workflow gate
```

CI runs the same gate on every push and pull request: `ruff check`,
`ruff format --check`, `pytest`, DAG compilation and `dbt parse`.

## Notes

- Python-independent, Docker-dependent pieces (Airflow scheduling, live Postgres
  load, `dbt build`, MinIO landing, Metabase dashboards) run end-to-end via
  Docker Compose on your machine; the test suite covers everything that does not
  require a running service.
- The full learning write-up behind this build lives in a separate guide repo.
