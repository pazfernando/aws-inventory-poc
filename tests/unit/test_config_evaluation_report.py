"""Verifies the evaluation report records all dimensions and one decision (3.1, 3.2)."""

from __future__ import annotations

from pathlib import Path

REPORT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "aws_lifecycle_inventory"
    / "inventory"
    / "config"
    / "EVALUATION_REPORT.md"
)

DIMENSIONS = [
    "Resource coverage",
    "Version completeness",
    "Freshness",
    "Latency",
    "API complexity",
    "Required IAM",
    "Operational dependencies",
    "Expected cost",
]

DECISIONS = ["DIRECT_API_PRIMARY", "HYBRID", "CONFIG_PRIMARY"]


def test_report_covers_every_dimension():
    text = REPORT.read_text()
    for dimension in DIMENSIONS:
        assert dimension in text, f"missing comparison dimension: {dimension}"


def test_report_records_exactly_one_decision():
    text = REPORT.read_text()
    # The "## Decision" section must name exactly one of the three outcomes as the
    # chosen strategy (other outcomes may be mentioned as impact on later changes).
    decision_section = text.split("## Decision", 1)[1]
    chosen = [d for d in DECISIONS if f"**{d}**" in decision_section]
    assert chosen == ["DIRECT_API_PRIMARY"], f"expected one bold decision, got {chosen}"


def test_report_states_impact_on_changes_06_07():
    text = REPORT.read_text()
    assert "Change 06" in text
    assert "Change 07" in text
