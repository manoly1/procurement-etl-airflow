-- Data layers, created on first Postgres start (docker-entrypoint-initdb.d).
--   raw     — ingested weekly snapshots (one row per key per week)
--   staging — transient load tables (rewritten each run)
--   marts   — BI-facing models (dbt, Stage 5)
--   meta    — pipeline metadata / run log (Stage 4)
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS meta;
