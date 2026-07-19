# datagen — synthetic extract generator (Stage 1)

Generates xlsx/csv files that mimic the structure of the real SAP `Open PO` and
`All PRs` extracts, plus CSV reference tables (seeds). "Dirty data" archetypes
(header not on row 1, numbers-as-text, leading zeros, duplicate rows, junk rows,
missing keys) are toggled by flags so tests can target each one.

Everything here is fully synthetic — no real values, paths, or identifiers.
