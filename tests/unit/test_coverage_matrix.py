"""Anti-drift test: coverage matrix must match registered collectors (task 3.2)."""

from __future__ import annotations

from pathlib import Path

from aws_lifecycle_inventory.inventory.direct_api import default_collectors

MATRIX_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "aws_lifecycle_inventory"
    / "inventory"
    / "direct_api"
    / "COVERAGE_MATRIX.md"
)


def _matrix_collectors() -> set[str]:
    """Collect the first-column values of the markdown table body."""
    names: set[str] = set()
    for line in MATRIX_PATH.read_text().splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        first = cells[0]
        # Skip the header row and the separator row.
        if first in {"collector", ""} or set(first) <= {"-", ":"}:
            continue
        names.add(first)
    return names


def test_coverage_matrix_matches_registered_collectors():
    registered = {c.name for c in default_collectors()}
    documented = _matrix_collectors()
    assert documented == registered, (
        f"coverage matrix drifted from collectors: "
        f"only in matrix={documented - registered}, "
        f"only in code={registered - documented}"
    )
