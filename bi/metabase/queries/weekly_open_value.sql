-- Dashboard card: "Open PO value by week" (line/bar chart).
-- Source: marts.mart_open_po_weekly (built by dbt). One point per reporting week.
select
    report_week,
    total_value_eur
from marts.mart_open_po_weekly
order by report_week
