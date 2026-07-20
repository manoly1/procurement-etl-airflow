"""Typer CLI for the synthetic data generator.

python -m datagen generate --dataset open_po --week 29
python -m datagen batch --weeks 25-30 --dataset all
python -m datagen seeds
"""

from __future__ import annotations

import typer

from .datasets import DATASETS
from .generate import generate_file
from .seeds import write_seeds

app = typer.Typer(
    help="Synthetic SAP-like extract generator (fully fake data).",
    no_args_is_help=True,
    add_completion=False,
)


def parse_weeks(spec: str) -> list[int]:
    """Parse "25-30", "29", or "25,27,29" into a sorted list of week numbers."""
    weeks: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = (int(x) for x in part.split("-", 1))
            weeks.update(range(lo, hi + 1))
        elif part:
            weeks.add(int(part))
    return sorted(weeks)


@app.command()
def generate(
    dataset: str = typer.Option(..., help="open_po | all_prs"),
    week: int = typer.Option(..., help="ISO week number"),
    dirty: bool = typer.Option(
        True, "--dirty/--clean", help="Inject dirty-data archetypes"
    ),
    out: str = typer.Option("data/raw", help="Output directory"),
    seed: int = typer.Option(None, help="Override the deterministic seed"),
) -> None:
    """Generate one extract file for a single dataset and week."""
    path = generate_file(dataset, week, dirty_on=dirty, out_dir=out, seed=seed)
    typer.echo(f"wrote {path}")


@app.command()
def batch(
    weeks: str = typer.Option("25-30", help='Weeks: "25-30", "29", or "25,27,29"'),
    dataset: str = typer.Option("all", help="open_po | all_prs | all"),
    dirty: bool = typer.Option(True, "--dirty/--clean"),
    out: str = typer.Option("data/raw"),
) -> None:
    """Generate many weeks of one or both datasets."""
    names = list(DATASETS) if dataset == "all" else [dataset]
    for wk in parse_weeks(weeks):
        for name in names:
            typer.echo(f"wrote {generate_file(name, wk, dirty_on=dirty, out_dir=out)}")


@app.command()
def seeds(
    out: str = typer.Option("seeds", help="Output directory for CSV seeds"),
) -> None:
    """Write the reference tables (responsibles, requisitioners, suppliers, rates)."""
    for path in write_seeds(out):
        typer.echo(f"wrote {path}")


if __name__ == "__main__":
    app()
