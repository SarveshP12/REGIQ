#!/usr/bin/env python3
"""Curate labeled TCC dataset from ITSM CSV, build vocabulary, and create splits."""

import argparse
import json
import sys
from pathlib import Path

# Allow running as script from apps/api
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.ai.dataset.prepare import DEFAULT_OUTPUT_DIR, DEFAULT_SOURCE_CSV, prepare_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare TCC classifier training dataset")
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE_CSV,
        help="Source CSV (default: docs/sample_data/Combined_500_ITSM_Test_Cases.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory (default: apps/api/data/datasets/tcc_v1)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for splits")
    args = parser.parse_args()

    manifest = prepare_dataset(source_csv=args.source, output_dir=args.output, seed=args.seed)
    print(json.dumps(manifest, indent=2))
    if not manifest["meets_minimum_2000"]:
        print(
            f"WARNING: only {manifest['counts']['total_labeled_examples']} examples "
            f"(minimum 2000 required)",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"\nDataset written to {args.output}")


if __name__ == "__main__":
    main()
