# etl — pipeline core (Stage 2+)

Standalone ETL that runs independently of the orchestrator:

    extract  -> find the header row in an untrusted xlsx
    resolve  -> map columns via YAML config (exact -> alias -> clear error)
    transform-> composite keys, ReportDate/ReportWeek, dedupe, lookup enrichment
    load     -> staging table -> INSERT ... ON CONFLICT (idempotent UPSERT)

Invoked the same way by the CLI (`python -m etl run ...`) and by the Airflow DAG.
