"""Stage logging — meta.etl_log (the Logger.LogStage analogue).

A tiny timer/record for each pipeline stage: module, stage, rows in/out,
duration, status. The record can be built and inspected without a database; the
write to ``meta.etl_log`` is done only when an engine is provided.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass


@dataclass
class StageRecord:
    module: str
    stage: str
    rows_in: int
    rows_out: int
    duration_s: float
    status: str


class StageTimer:
    """Context manager that times a stage and captures its outcome.

    with StageTimer("transform", "dedup", rows_in=len(df)) as t:
        result = do_work()
        t.rows_out = len(result)
    record = t.record()  # status is PASSED, or FAILED if the block raised
    """

    def __init__(self, module: str, stage: str, rows_in: int = 0) -> None:
        self.module = module
        self.stage = stage
        self.rows_in = rows_in
        self.rows_out = 0
        self.status = "PASSED"
        self.duration_s = 0.0
        self._start = 0.0

    def __enter__(self) -> StageTimer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.duration_s = time.perf_counter() - self._start
        if exc_type is not None:
            self.status = "FAILED"
        return False  # never suppress the exception

    def record(self) -> StageRecord:
        return StageRecord(
            module=self.module,
            stage=self.stage,
            rows_in=self.rows_in,
            rows_out=self.rows_out,
            duration_s=round(self.duration_s, 4),
            status=self.status,
        )


def write_log(engine, record: StageRecord) -> None:
    """Persist a stage record to meta.etl_log (requires a live engine)."""
    from sqlalchemy import text

    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO meta.etl_log "
                "(module, stage, rows_in, rows_out, duration_s, status) "
                "VALUES (:module, :stage, :rows_in, :rows_out, :duration_s, :status)"
            ),
            asdict(record),
        )
