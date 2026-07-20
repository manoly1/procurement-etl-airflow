# dags — Airflow DAGs (Stage 3)

`weekly_procurement_etl`: schedule `0 9 * * 1`, a file sensor, and per-branch
fail-fast dependencies mirroring the original Power Automate chain. The run's
logical date (`data_interval_start`) drives the reporting week — the direct
analogue of `Config.WeekToReportDate`.
