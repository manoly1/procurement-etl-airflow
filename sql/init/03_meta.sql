-- Run log: one row per pipeline stage per run (the Logger.LogStage analogue).
CREATE TABLE IF NOT EXISTS meta.etl_log (
    id          bigserial PRIMARY KEY,
    module      text,
    stage       text,
    rows_in     integer,
    rows_out    integer,
    duration_s  double precision,
    status      text,
    started_at  timestamptz DEFAULT now()
);
