## What

<!-- One or two sentences: what does this change do and why. -->

## Changes

<!-- Bullet the notable changes. -->

## Verification

<!-- How you know it works. Tick what you ran. -->

- [ ] `make lint` (ruff check) clean
- [ ] `make fmt` (ruff format) clean
- [ ] `make test` (pytest) green
- [ ] `make checkpoint N` passes for the touched stage
- [ ] Docker-dependent parts (Airflow / Postgres / dbt / MinIO / Metabase) run locally if changed
