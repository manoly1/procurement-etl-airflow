with source as (
    select * from {{ source('raw', 'open_po') }}
)

select
    (report_week::text || '-' || key) as row_id,
    report_week,
    key,
    po_number,
    po_item,
    material,
    material_description,
    supplier,
    order_quantity,
    net_price,
    currency,
    rate_to_eur,
    line_value_eur,
    report_date::date as report_date
from source
