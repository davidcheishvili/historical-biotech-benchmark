# Historical Biotech Benchmark — public reproducibility code

This repository contains Python code associated with the Data Descriptor:

**A point-in-time benchmark of 2,604 therapeutic biotechnology program-stage records with 36-month development outcomes**

## Dataset

Associated public dataset: **Zenodo DOI 10.5281/zenodo.23201979**

## Included scripts

- `validate_release.py` — validates the released 19-field core dataset.
- `validate_provenance.py` — validates the outcome-provenance companion and its one-to-one join with the core dataset.
- `summarize_release.py` — regenerates descriptive summaries from the released core dataset.
- `build_public_release.py` — constructs the publication-facing CSV files from the frozen curated source tables used for the release.

## Requirements

Python 3.9 or later. No third-party Python packages are required.

## Validation

```bash
python validate_release.py historical_biotech_benchmark_core.csv
python validate_provenance.py historical_biotech_benchmark_core.csv historical_biotech_benchmark_outcome_provenance.csv
```

Expected outputs:

```text
PASS: public core integrity
PASS: outcome provenance integrity and 2,604-row join
```

## Descriptive summaries

```bash
python summarize_release.py historical_biotech_benchmark_core.csv summaries
```

## Reconstruct the publication release

```bash
python build_public_release.py <source_analysis.csv> <source_outcome_ledger.csv> <output_dir>
```

The required source tables are frozen curated research records used during preparation of the publication release. They contain internal working fields and are not distributed as part of the public dataset. The released CSV files can be independently validated with the public validation scripts.

## Scope

This repository does not contain the private Risk Platform application, proprietary assessment variables, internal workflow infrastructure, or later development material.

## License

Code: MIT License. Dataset: CC BY 4.0.
