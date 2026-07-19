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
