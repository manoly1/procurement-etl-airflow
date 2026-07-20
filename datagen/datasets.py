"""Synthetic dataset definitions.

Anonymized column layouts that mirror the *structure* of the real SAP `Open PO`
and `All PRs` extracts — without any real header names, values, or identifiers.
Composite keys match the PRKey / POKey idea from the original project.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Dataset:
    """Structural description of one synthetic extract."""

    name: str
    columns: tuple[str, ...]  # ordered header names
    key_cols: tuple[str, ...]  # composite key (e.g. number + item)
    numeric_cols: tuple[str, ...]  # columns eligible for the numbers-as-text dirt
    material_col: str  # column carrying leading-zero material keys
    date_col: str  # a date column (for realistic values)


OPEN_PO = Dataset(
    name="open_po",
    columns=(
        "PO Number",
        "PO Item",
        "Material",
        "Material Description",
        "Supplier",
        "Order Quantity",
        "Net Price",
        "Currency",
        "Delivery Date",
        "Plant",
        "Requisitioner",
    ),
    key_cols=("PO Number", "PO Item"),
    numeric_cols=("Order Quantity", "Net Price"),
    material_col="Material",
    date_col="Delivery Date",
)

ALL_PRS = Dataset(
    name="all_prs",
    columns=(
        "PR Number",
        "PR Item",
        "Material",
        "Material Description",
        "Requested Quantity",
        "Requisitioner",
        "Responsible",
        "Release Date",
        "Plant",
    ),
    key_cols=("PR Number", "PR Item"),
    numeric_cols=("Requested Quantity",),
    material_col="Material",
    date_col="Release Date",
)

DATASETS: dict[str, Dataset] = {d.name: d for d in (OPEN_PO, ALL_PRS)}
