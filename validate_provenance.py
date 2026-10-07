#!/usr/bin/env python3
"""Validate the public outcome-provenance companion against the core dataset."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def read_csv(path: str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main(core_path: str, provenance_path: str) -> int:
    core_file = Path(core_path)
    provenance_file = Path(provenance_path)

    if not core_file.is_file():
        print(f"ERROR: file not found: {core_file}", file=sys.stderr)
        return 2
    if not provenance_file.is_file():
        print(f"ERROR: file not found: {provenance_file}", file=sys.stderr)
        return 2

    core = read_csv(core_path)
    provenance = read_csv(provenance_path)

    assert len(core) == 2604
    assert len(provenance) == 2604

    core_by_id = {row["record_id"]: row for row in core}
    provenance_by_id = {row["record_id"]: row for row in provenance}

    assert len(core_by_id) == 2604
    assert len(provenance_by_id) == 2604
    assert set(core_by_id) == set(provenance_by_id)

    reconstructed = {
        record_id
        for record_id, row in core_by_id.items()
        if row["historical_reconstruction_status"] == "Reconstructed"
    }
    assert len(reconstructed) == 1972

    assert sum(
        bool(provenance_by_id[record_id]["outcome_source_url_1"])
        for record_id in reconstructed
    ) == 1972

    assert sum(
        bool(provenance_by_id[record_id]["outcome_source_url_2"])
        for record_id in reconstructed
    ) == 1653

    non_reconstructed = set(core_by_id) - reconstructed
    assert all(
        not provenance_by_id[record_id]["outcome_source_url_1"]
        and not provenance_by_id[record_id]["outcome_source_url_2"]
        for record_id in non_reconstructed
    )

    for row in provenance:
        for field in ("outcome_source_url_1", "outcome_source_url_2"):
            value = row[field]
            assert not value or value.startswith(("http://", "https://"))

        expected_count = int(bool(row["outcome_source_url_1"])) + int(
            bool(row["outcome_source_url_2"])
        )
        assert row["outcome_source_count"] == str(expected_count)

    print("PASS: outcome provenance integrity and 2,604-row join")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python validate_provenance.py <core.csv> <outcome_provenance.csv>",
            file=sys.stderr,
        )
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
