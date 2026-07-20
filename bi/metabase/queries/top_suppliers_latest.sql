-- Dashboard card: "Top 10 suppliers by open value (latest week)" (row chart).
-- Uses the most recent reporting week present in the mart, so the card stays
-- correct as new weeks load — no hardcoded week.
select
    supplier,
    value_eur
from marts.mart_top_suppliers
where report_week = (select max(report_week) from marts.mart_top_suppliers)
order by value_eur desc
limit 10
