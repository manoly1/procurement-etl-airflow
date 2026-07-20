-- Dashboard card: "Open PO line count by week" (bar chart).
-- Tracks volume of open lines week over week — a spike/drop is worth a look.
select
    report_week,
    line_count
from marts.mart_open_po_weekly
order by report_week
