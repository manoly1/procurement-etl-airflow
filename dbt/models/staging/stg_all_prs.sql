with source as (
    select * from {{ source('raw', 'all_prs') }}
)

select
    (report_week::text || '-' || key) as row_id,
    report_week,
    key,
    pr_number,
    pr_item,
    material,
    material_description,
    requested_quantity,
    requisitioner,
    responsible,
    report_date::date as report_date
from source
