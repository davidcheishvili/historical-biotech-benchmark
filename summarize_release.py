#!/usr/bin/env python3
"""Generate descriptive summaries for the Historical Biotech Benchmark release."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

STAGES = ["Phase I", "Phase II", "Phase III / pivotal"]


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def main(input_csv: str, output_dir: str) -> int:
    src = Path(input_csv)
    if not src.is_file():
        print(f"ERROR: file not found: {src}", file=sys.stderr)
        return 2

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    with src.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    cohort_rows: list[list[object]] = []
    for stage in STAGES:
        stage_rows = [row for row in rows if row["index_stage"] == stage]
        cohort_rows.append([
            stage,
            len(stage_rows),
            sum(row["historical_reconstruction_status"] == "Reconstructed" for row in stage_rows),
            sum(row["outcome_evaluable"] == "Yes" for row in stage_rows),
            sum(row["y36"] == "1" for row in stage_rows),
        ])

    cohort_rows.append([
        "Total",
        len(rows),
        sum(row["historical_reconstruction_status"] == "Reconstructed" for row in rows),
        sum(row["outcome_evaluable"] == "Yes" for row in rows),
        sum(row["y36"] == "1" for row in rows),
    ])

    write_csv(
        out / "cohort_composition_by_stage.csv",
        [
            "development_stage",
            "total_records",
            "reconstructed_n",
            "outcome_evaluable_n",
            "successful_transition_36m_n",
        ],
        cohort_rows,
    )

    outcome_counts = Counter(row["outcome_36m_status"] for row in rows)
    write_csv(
        out / "outcome_states.csv",
        ["outcome_36m_status", "n"],
        [[key, value] for key, value in sorted(outcome_counts.items())],
    )

    source_counts = Counter(
        row["index_source_category"]
        for row in rows
        if row["historical_reconstruction_status"] == "Reconstructed"
    )
    write_csv(
        out / "index_source_categories.csv",
        ["index_source_category", "n"],
        [[key, value] for key, value in sorted(source_counts.items())],
    )

    print(f"PASS: descriptive summaries written to {out}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python summarize_release.py <core_release.csv> <output_dir>",
            file=sys.stderr,
        )
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
