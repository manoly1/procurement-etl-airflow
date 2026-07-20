-- Weekly Open PO KPIs: line count and value per reporting week.
select
    report_week,
    max(report_date) as report_date,
    count(*) as line_count,
    sum(order_quantity) as total_quantity,
    sum(line_value_eur) as total_value_eur
from {{ ref('stg_open_po') }}
group by report_week
order by report_week
