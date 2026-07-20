-- Supplier ranking by open-PO value per reporting week.
select
    report_week,
    supplier,
    count(*) as line_count,
    sum(line_value_eur) as value_eur
from {{ ref('stg_open_po') }}
group by report_week, supplier
order by report_week, value_eur desc
