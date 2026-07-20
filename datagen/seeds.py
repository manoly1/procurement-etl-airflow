"""Reference tables ("seeds").

Small lookup tables (responsible persons, requisitioners, suppliers, currency
rates) that the pipeline later joins onto the fact rows — the analogue of the
manual lookup files in the original project. Fully synthetic, generated with a
fixed seed so they are reproducible.
"""

from __future__ import annotations

import pandas as pd
from faker import Faker

CURRENCIES = ("EUR", "USD", "GBP", "PLN")
PLANTS = ("P100", "P200", "P300")


def build_seeds(
    seed: int = 20260720, n_people: int = 12, n_suppliers: int = 20
) -> dict[str, pd.DataFrame]:
    """Build the reference tables as DataFrames, deterministically."""
    fake = Faker("en_US")
    fake.seed_instance(seed)

    people = [fake.unique.name() for _ in range(n_people)]
    responsibles = pd.DataFrame(
        {
            "person": people,
            "team": [
                fake.random_element(("Direct", "Indirect", "MRO")) for _ in people
            ],
        }
    )
    requisitioners = pd.DataFrame(
        {"person": people, "plant": [fake.random_element(PLANTS) for _ in people]}
    )
    suppliers = pd.DataFrame(
        {
            "supplier": [fake.unique.company() for _ in range(n_suppliers)],
            "country": [fake.country_code() for _ in range(n_suppliers)],
        }
    )
    rates = pd.DataFrame(
        {
            "currency": CURRENCIES,
            "rate_to_eur": [1.00, 0.92, 1.17, 0.23],
        }
    )
    return {
        "responsibles": responsibles,
        "requisitioners": requisitioners,
        "suppliers": suppliers,
        "rates": rates,
    }


def write_seeds(out_dir: str, seed: int = 20260720) -> list[str]:
    """Write the seed tables as CSV files; return the paths written."""
    from pathlib import Path

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for name, df in build_seeds(seed).items():
        path = out / f"{name}.csv"
        df.to_csv(path, index=False)
        written.append(str(path))
    return written
