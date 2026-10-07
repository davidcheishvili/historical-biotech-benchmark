#!/usr/bin/env python3
"""Build the publication-facing Historical Biotech Benchmark release files."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

OUTCOME_MAP = {
    "SUCCESSFUL_PROGRESSION": "Successful transition within 36 months",
    "ONGOING_UNRESOLVED": "No qualifying transition by 36-month horizon",
    "SCIENTIFIC_EFFICACY_FAILURE": "Scientific / efficacy failure",
    "TECHNICAL_CMC_FAILURE": "Technical / CMC failure",
    "SAFETY_FAILURE": "Safety failure",
    "REGULATORY_FAILURE": "Regulatory failure",
    "STRATEGIC_FINANCIAL_STOP": "Strategic / financial stop",
    "UNKNOWN_REASON": "Stop / failure reason uncertain",
    "OUTCOME_NON_EVALUABLE": "Outcome non-evaluable",
}

PUBLIC_FIELDS = [
    "record_id", "company", "program", "indication", "index_stage", "nct_id",
    "index_date", "era", "historical_reconstruction_status",
    "inclusion_probability", "design_weight", "outcome_36m_status", "y36",
    "outcome_event_date", "outcome_evaluable", "outcome_adjudication_confidence",
    "outcome_horizon_36m_end_date", "index_source_category", "index_source_locator",
]

PROVENANCE_FIELDS = [
    "record_id", "historical_reconstruction_status", "outcome_36m_status",
    "outcome_source_url_1", "outcome_source_date_1", "outcome_source_date_type_1",
    "outcome_source_url_2", "outcome_source_date_2", "outcome_source_date_type_2",
    "outcome_source_count",
]

URL_RE = re.compile(r"https?://[^;\s]+")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def source_category(raw: str) -> str:
    if not raw:
        return ""
    upper = raw.upper()
    if "PUBLICATION" in upper and "SPONSOR_OR_PUBLICATION" not in upper:
        return "Contemporaneous publication"
    if "SPONSOR" in upper:
        return "Sponsor contemporaneous disclosure"
    return "ClinicalTrials.gov historical record"


def public_index_locator(category: str, raw_locator: str, nct_id: str) -> str:
    if not category:
        return ""
    if category == "ClinicalTrials.gov historical record":
        return f"https://clinicaltrials.gov/study/{nct_id}"
    urls = URL_RE.findall(raw_locator or "")
    if urls:
        return " ; ".join(urls)
    return f"https://clinicaltrials.gov/study/{nct_id}"


def era_from_date(value: str) -> str:
    if not value:
        return "Not reconstructed"
    return "2015–2019" if int(value[:4]) <= 2019 else "2020–2022"


def build_core(source_analysis: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    for row in source_analysis:
        reconstructed = row["out_authoritative_resolution_status"] == "RESOLVED"
        category = (
            source_category(row["out_authoritative_index_source_type"])
            if reconstructed
            else ""
        )
        raw_outcome = row["out_outcome_class"] if reconstructed else ""

        rows.append({
            "record_id": row["historical_case_id"],
            "company": row["pred_company_name_at_index"],
            "program": row["pred_program_asset_at_index"],
            "indication": row["pred_indication_at_index"],
            "index_stage": row["pred_index_stage"],
            "nct_id": row["out_source_nct_id"],
            "index_date": row["out_authoritative_index_date"] if reconstructed else "",
            "era": (
                era_from_date(row["out_authoritative_index_date"])
                if reconstructed
                else "Not reconstructed"
            ),
            "historical_reconstruction_status": (
                "Reconstructed"
                if reconstructed
                else "Historical index not reconstructable under frozen protocol"
            ),
            "inclusion_probability": row["pred_target_unit_inclusion_probability"],
            "design_weight": row["pred_target_unit_design_weight"],
            "outcome_36m_status": OUTCOME_MAP.get(
                raw_outcome,
                "Not adjudicated — no authoritative historical index date",
            ),
            "y36": row["out_y36"] if row["out_analysis_y36_evaluable"] == "YES" else "",
            "outcome_event_date": row["out_outcome_event_date"] if reconstructed else "",
            "outcome_evaluable": (
                "Yes" if row["out_analysis_y36_evaluable"] == "YES" else "No"
            ),
            "outcome_adjudication_confidence": (
                row["out_adjudication_confidence"] if reconstructed else ""
            ),
            "outcome_horizon_36m_end_date": (
                row["out_outcome_horizon_36m_end_date"] if reconstructed else ""
            ),
            "index_source_category": category,
            "index_source_locator": (
                public_index_locator(
                    category,
                    row["out_authoritative_index_source_locator"],
                    row["out_source_nct_id"],
                )
                if reconstructed
                else ""
            ),
        })

    return rows


def build_provenance(
    core: list[dict[str, str]],
    source_outcomes: list[dict[str, str]],
) -> list[dict[str, str]]:
    source_by_id = {row["historical_case_id"]: row for row in source_outcomes}
    result: list[dict[str, str]] = []

    for core_row in core:
        source_row = source_by_id.get(core_row["record_id"], {})
        url_1 = source_row.get("outcome_source_url_1", "")
        url_2 = source_row.get("outcome_source_url_2", "")

        result.append({
            "record_id": core_row["record_id"],
            "historical_reconstruction_status": core_row[
                "historical_reconstruction_status"
            ],
            "outcome_36m_status": core_row["outcome_36m_status"],
            "outcome_source_url_1": url_1,
            "outcome_source_date_1": source_row.get("outcome_source_date_1", ""),
            "outcome_source_date_type_1": source_row.get(
                "outcome_source_date_type_1", ""
            ),
            "outcome_source_url_2": url_2,
            "outcome_source_date_2": source_row.get("outcome_source_date_2", ""),
            "outcome_source_date_type_2": source_row.get(
                "outcome_source_date_type_2", ""
            ),
            "outcome_source_count": str(int(bool(url_1)) + int(bool(url_2))),
        })

    return result


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(analysis_path: str, outcome_path: str, output_dir: str) -> int:
    analysis_file = Path(analysis_path)
    outcome_file = Path(outcome_path)

    if not analysis_file.is_file():
        print(f"ERROR: file not found: {analysis_file}", file=sys.stderr)
        return 2
    if not outcome_file.is_file():
        print(f"ERROR: file not found: {outcome_file}", file=sys.stderr)
        return 2

    core = build_core(read_csv(analysis_file))
    provenance = build_provenance(core, read_csv(outcome_file))

    assert len(core) == 2604
    assert len({row["record_id"] for row in core}) == 2604
    assert sum(
        row["historical_reconstruction_status"] == "Reconstructed" for row in core
    ) == 1972
    assert sum(row["y36"] == "1" for row in core) == 303
    assert sum(row["y36"] == "0" for row in core) == 1247
    assert not any(
        "drive.google" in row["index_source_locator"].lower()
        or "Drive " in row["index_source_locator"]
        for row in core
    )
    assert sum(bool(row["outcome_source_url_1"]) for row in provenance) == 1972

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    write_csv(out / "historical_biotech_benchmark_core.csv", PUBLIC_FIELDS, core)
    write_csv(
        out / "historical_biotech_benchmark_outcome_provenance.csv",
        PROVENANCE_FIELDS,
        provenance,
    )

    print(
        f"PASS: wrote {len(core)} core rows and "
        f"{len(provenance)} provenance rows to {out}"
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: python build_public_release.py "
            "<source_analysis.csv> <source_outcome_ledger.csv> <output_dir>",
            file=sys.stderr,
        )
        raise SystemExit(2)

    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
