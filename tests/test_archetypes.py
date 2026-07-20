"""The dataset x dirty-archetype matrix (V4-audit idea, as code)."""

from __future__ import annotations


def test_archetype_matrix_cell(single_archetype):
    name, dataset, clean, dirtied = single_archetype
    # Applying a single archetype never changes the column set.
    assert list(dirtied.columns) == list(dataset.columns)
    # date_in_row1 is writer-level (no frame change); every other archetype
    # visibly changes the frame's contents or shape.
    if name == "date_in_row1":
        assert dirtied.equals(clean)
    else:
        assert dirtied.shape != clean.shape or not dirtied.equals(clean)
