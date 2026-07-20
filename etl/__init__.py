"""ETL core (Stage 2+).

Standalone pipeline that runs with or without Airflow — the same code the DAG
calls can be invoked from the CLI (`python -m etl ...`). Mirrors the
RunMacro.vbs / *_Headless split from the original VBA project.
"""
