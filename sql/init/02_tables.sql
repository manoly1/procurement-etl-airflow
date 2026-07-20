-- Target tables for the weekly snapshots. The primary key is (report_week, key):
-- one row per business key per reporting week. This is what makes re-loading a
-- week idempotent — the UPSERT updates existing rows instead of appending.

CREATE TABLE IF NOT EXISTS raw.open_po (
    report_week          integer NOT NULL,
    key                  text    NOT NULL,
    po_number            text,
    po_item              text,
    material             text,
    material_description text,
    supplier             text,
    order_quantity       double precision,
    net_price            double precision,
    currency             text,
    delivery_date        text,
    plant                text,
    requisitioner        text,
    report_date          text,
    rate_to_eur          double precision,
    line_value_eur       double precision,
    PRIMARY KEY (report_week, key)
);

CREATE TABLE IF NOT EXISTS raw.all_prs (
    report_week          integer NOT NULL,
    key                  text    NOT NULL,
    pr_number            text,
    pr_item              text,
    material             text,
    material_description text,
    requested_quantity   double precision,
    requisitioner        text,
    responsible          text,
    release_date         text,
    plant                text,
    report_date          text,
    PRIMARY KEY (report_week, key)
);
