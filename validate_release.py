#!/usr/bin/env python3
"""Validate the released Historical Biotech Benchmark core dataset."""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

FIELDS = [
    "record_id", "company", "program", "indication", "index_stage", "nct_id",
    "index_date", "era", "historical_reconstruction_status",
    "inclusion_probability", "design_weight", "outcome_36m_status", "y36",
    "outcome_event_date", "outcome_evaluable", "outcome_adjudication_confidence",
    "outcome_horizon_36m_end_date", "index_source_category", "index_source_locator",
]

EXPECTED = {
    "records": 2604,
    "companies": 1155,
    "nct_ids": 2544,
    "reconstructed": 1972,
    "outcome_evaluable": 1550,
    "y36_1": 303,
    "y36_0": 1247,
    "outcome_non_evaluable": 422,
}

EXPECTED_STAGE_COUNTS = Counter(
    {"Phase I": 920, "Phase II": 984, "Phase III / pivotal": 700}
)

NCT_RE = re.compile(r"^NCT\d{8}$")
YEAR_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
YEAR_RE = re.compile(r"^\d{4}$")


def valid_full_date(value: str) -> bool:
    if not value:
        return True
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def valid_event_date(value: str) -> bool:
    if not value:
        return True
    if YEAR_RE.fullmatch(value):
        return True
    if YEAR_MONTH_RE.fullmatch(value):
        year, month = map(int, value.split("-"))
        return 1 <= year <= 9999 and 1 <= month <= 12
    return valid_full_date(value)


def main(path: str) -> int:
    src = Path(path)
    if not src.is_file():
        print(f"ERROR: file not found: {src}", file=sys.stderr)
        return 2

    with src.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == FIELDS, (
            f"Schema mismatch. Expected {FIELDS!r}; got {reader.fieldnames!r}"
        )
        rows = list(reader)

    assert len(rows) == EXPECTED["records"]
    assert len({row["record_id"] for row in rows}) == EXPECTED["records"]
    assert len({row["company"] for row in rows}) == EXPECTED["companies"]
    assert len({row["nct_id"] for row in rows}) == EXPECTED["nct_ids"]
    assert all(NCT_RE.fullmatch(row["nct_id"]) for row in rows)

    stage_counts = Counter(row["index_stage"] for row in rows)
    assert stage_counts == EXPECTED_STAGE_COUNTS, f"Stage counts mismatch: {stage_counts}"

    assert sum(
        row["historical_reconstruction_status"] == "Reconstructed" for row in rows
    ) == EXPECTED["reconstructed"]

    assert sum(row["outcome_evaluable"] == "Yes" for row in rows) == EXPECTED["outcome_evaluable"]
    assert sum(row["y36"] == "1" for row in rows) == EXPECTED["y36_1"]
    assert sum(row["y36"] == "0" for row in rows) == EXPECTED["y36_0"]
    assert sum(
        row["outcome_36m_status"] == "Outcome non-evaluable" for row in rows
    ) == EXPECTED["outcome_non_evaluable"]

    for row in rows:
        assert valid_full_date(row["index_date"])
        assert valid_full_date(row["outcome_horizon_36m_end_date"])
        assert valid_event_date(row["outcome_event_date"])

        if row["outcome_evaluable"] == "Yes":
            assert row["y36"] in {"0", "1"}
        else:
            assert row["y36"] == ""

        if row["historical_reconstruction_status"] != "Reconstructed":
            assert row["index_date"] == ""

    assert not any(
        "drive.google" in row["index_source_locator"].lower()
        or "Drive " in row["index_source_locator"]
        for row in rows
    )

    print("PASS: public core integrity")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_release.py <core_release.csv>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
