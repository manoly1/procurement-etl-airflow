-- Dashboard card: single-number KPIs for the latest reporting week.
-- Total open value, total quantity and line count at a glance.
select
    report_week,
    line_count,
    total_quantity,
    total_value_eur
from marts.mart_open_po_weekly
where report_week = (select max(report_week) from marts.mart_open_po_weekly)
