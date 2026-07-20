"""Shared fixtures: valid snapshots and the dataset x dirty-archetype matrix.

The `single_archetype` fixture is the systematic version of the V4 audit: every
dataset crossed with every dirty archetype, one archetype at a time.
"""

from __future__ import annotations

import random

import pytest

from datagen import dirty
from datagen.datasets import DATASETS
from datagen.generate import generate_file, generate_frame
from datagen.seeds import build_seeds
from etl.pipeline import build_snapshot_for

DATASET_NAMES = ("open_po", "all_prs")


@pytest.fixture(params=DATASET_NAMES)
def dataset(request):
    return DATASETS[request.param]


@pytest.fixture
def snapshot(dataset, tmp_path):
    """A valid weekly snapshot — passes all quality checks."""
    path = generate_file(dataset.name, 29, dirty_on=True, out_dir=str(tmp_path))
    return build_snapshot_for(dataset.name, path, 29, seeds=build_seeds())


@pytest.fixture(params=list(dirty.DIRTY_ARCHETYPES))
def single_archetype(request, dataset):
    """A frame with exactly one dirty archetype applied."""
    clean, _ = generate_frame(dataset.name, 29, dirty_on=False, seed=1)
    dirtied = dirty.apply(clean, dataset, {request.param}, random.Random(1))
    return request.param, dataset, clean, dirtied
