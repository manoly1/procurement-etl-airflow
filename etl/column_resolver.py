"""Declarative column mapping — the Python analogue of ColumnResolver.

A dataset's columns are described in YAML (``config/datasets/<name>.yml``): each
canonical field names its source header plus optional aliases. The resolver maps
whatever headers a file actually has onto the canonical names, following an
``exact -> alias -> clear error`` strategy. Unlike the VBA version, a missing
required column fails fast with a descriptive report instead of prompting the
user (an interactive prompt is an anti-pattern in automation).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml


class ColumnResolutionError(ValueError):
    """Raised when a required column cannot be mapped to any source header."""


@dataclass(frozen=True)
class ColumnSpec:
    field: str
    header: str
    aliases: tuple[str, ...] = ()
    required: bool = False


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    key: tuple[str, ...]
    columns: tuple[ColumnSpec, ...]

    def known_headers(self) -> set[str]:
        """Every source header this dataset might use (header + all aliases)."""
        names: set[str] = set()
        for spec in self.columns:
            names.add(spec.header)
            names.update(spec.aliases)
        return names


def load_config(path: str | Path) -> DatasetConfig:
    """Load a dataset column-mapping config from YAML."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    columns = tuple(
        ColumnSpec(
            field=fieldname,
            header=spec["header"],
            aliases=tuple(spec.get("aliases", []) or ()),
            required=bool(spec.get("required", False)),
        )
        for fieldname, spec in data["columns"].items()
    )
    return DatasetConfig(
        name=data["name"],
        key=tuple(data["key"]),
        columns=columns,
    )


def load_dataset_config(
    name: str, config_dir: str | Path = "config/datasets"
) -> DatasetConfig:
    """Load a config by dataset name from the standard config directory."""
    return load_config(Path(config_dir) / f"{name}.yml")


@dataclass
class Resolution:
    """The result of resolving a file's columns against a config."""

    mapping: dict[str, str] = field(
        default_factory=dict
    )  # canonical field -> source header
    missing_optional: list[str] = field(default_factory=list)


def resolve_columns(source_columns: Iterable[str], config: DatasetConfig) -> Resolution:
    """Map canonical fields onto the source columns present in a file.

    exact header -> first matching alias -> error (required) / skip (optional).
    """
    present = {str(c).strip(): str(c) for c in source_columns if c is not None}
    resolution = Resolution()
    for spec in config.columns:
        match = None
        if spec.header in present:
            match = present[spec.header]
        else:
            for alias in spec.aliases:
                if alias in present:
                    match = present[alias]
                    break
        if match is not None:
            resolution.mapping[spec.field] = match
        elif spec.required:
            raise ColumnResolutionError(
                f"[{config.name}] required column {spec.field!r} not found: "
                f"tried header {spec.header!r} and aliases {list(spec.aliases)}. "
                f"Available columns: {sorted(present)}"
            )
        else:
            resolution.missing_optional.append(spec.field)
    return resolution


def apply_resolution(df: pd.DataFrame, resolution: Resolution) -> pd.DataFrame:
    """Return a frame with only the resolved columns, renamed to canonical fields."""
    rename = {source: fieldname for fieldname, source in resolution.mapping.items()}
    out = df[list(rename)].rename(columns=rename)
    return out.reset_index(drop=True)
