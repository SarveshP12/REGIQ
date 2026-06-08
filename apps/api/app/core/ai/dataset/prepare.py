"""Prepare labeled TCC training dataset from ITSM test case CSV exports."""

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from app.core.ai.dataset.itsm_vocabulary import build_vocabulary, save_vocabulary
from app.core.ai.dataset.label_hierarchy import LABEL_HIERARCHY, build_labels_for_row

_REPO_ROOT = Path(__file__).resolve().parents[6]
_API_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SOURCE_CSV = _REPO_ROOT / "docs" / "sample_data" / "Combined_500_ITSM_Test_Cases.csv"
DEFAULT_OUTPUT_DIR = _API_ROOT / "data" / "datasets" / "tcc_v1"

SPLIT_RATIOS = (0.70, 0.15, 0.15)
MIN_LABELED_EXAMPLES = 2000
RANDOM_SEED = 42


@dataclass
class LabeledExample:
    id: str
    granularity: str  # test_case | step
    text: str
    labels: dict[str, str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "granularity": self.granularity,
            "text": self.text,
            "labels": self.labels,
            "metadata": self.metadata,
        }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _aggregate_test_cases(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        tc_name = row.get("Test Case Name", "").strip()
        if not tc_name:
            continue
        grouped[tc_name].append(row)
    return grouped


def _build_test_case_text(tc_name: str, step_rows: list[dict[str, str]]) -> str:
    first = step_rows[0]
    parts = [
        f"Test Case: {tc_name}",
        f"Scenario: {first.get('Test Scenario Detail', '')}",
        f"Description: {first.get('Test Case Description', '')}",
        f"Section: {first.get('Reference Section from Document', '')}",
        f"Subsection: {first.get('Reference Subsection from Document', '')}",
        "Steps:",
    ]
    for row in sorted(step_rows, key=lambda r: int(r.get("Step Number") or 0)):
        sn = row.get("Step Number", "")
        parts.append(
            f"  {sn}. {row.get('Step Description', '')} => {row.get('Expected Result', '')}"
        )
    return "\n".join(p for p in parts if p.strip())


def curate_examples(rows: list[dict[str, str]]) -> list[LabeledExample]:
    """Build labeled examples at test-case and step granularity."""
    examples: list[LabeledExample] = []
    grouped = _aggregate_test_cases(rows)

    for tc_name, step_rows in grouped.items():
        first = step_rows[0]
        labels = build_labels_for_row(first)
        tc_text = _build_test_case_text(tc_name, step_rows)

        examples.append(
            LabeledExample(
                id=tc_name,
                granularity="test_case",
                text=tc_text,
                labels=labels,
                metadata={
                    "reference_section": first.get("Reference Section from Document"),
                    "reference_subsection": first.get("Reference Subsection from Document"),
                    "raw_business_process": first.get("Business Process of Section"),
                    "step_count": len(step_rows),
                },
            )
        )

        for row in step_rows:
            step_num = row.get("Step Number", "0")
            step_id = f"{tc_name}::step::{step_num}"
            step_text = (
                f"{row.get('Test Scenario Detail', '')}. "
                f"{row.get('Step Description', '')}. "
                f"Expected: {row.get('Expected Result', '')}. "
                f"Context: {row.get('Reference Section from Document', '')} / "
                f"{row.get('Business Process of Section', '')}"
            )
            examples.append(
                LabeledExample(
                    id=step_id,
                    granularity="step",
                    text=step_text.strip(),
                    labels=build_labels_for_row(row),
                    metadata={
                        "parent_test_case": tc_name,
                        "step_number": step_num,
                    },
                )
            )

    return examples


def stratified_split(
    examples: list[LabeledExample],
    ratios: tuple[float, float, float] = SPLIT_RATIOS,
    seed: int = RANDOM_SEED,
) -> dict[str, list[LabeledExample]]:
    """Split by parent test case (avoid step leakage across splits)."""
    tc_examples = [e for e in examples if e.granularity == "test_case"]
    step_by_parent: dict[str, list[LabeledExample]] = defaultdict(list)
    for e in examples:
        if e.granularity == "step":
            parent = e.metadata.get("parent_test_case", "")
            step_by_parent[parent].append(e)

    # Stratify on business_process
    buckets: dict[str, list[LabeledExample]] = defaultdict(list)
    for tc in tc_examples:
        bp = tc.labels.get("business_process", "Other")
        buckets[bp].append(tc)

    rng = random.Random(seed)
    train_tc: list[LabeledExample] = []
    val_tc: list[LabeledExample] = []
    test_tc: list[LabeledExample] = []

    for _bp, bucket in buckets.items():
        rng.shuffle(bucket)
        n = len(bucket)
        n_train = int(n * ratios[0])
        n_val = int(n * ratios[1])
        n_test = n - n_train - n_val
        train_tc.extend(bucket[:n_train])
        val_tc.extend(bucket[n_train : n_train + n_val])
        test_tc.extend(bucket[n_train + n_val :])

    def expand_with_steps(tc_list: list[LabeledExample]) -> list[LabeledExample]:
        out: list[LabeledExample] = []
        for tc in tc_list:
            out.append(tc)
            out.extend(step_by_parent.get(tc.id, []))
        return out

    return {
        "train": expand_with_steps(train_tc),
        "validation": expand_with_steps(val_tc),
        "test": expand_with_steps(test_tc),
    }


def _write_jsonl(path: Path, examples: list[LabeledExample]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex.to_dict(), ensure_ascii=False) + "\n")


def prepare_dataset(
    source_csv: Path | None = None,
    output_dir: Path | None = None,
    seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    """Full pipeline: curate, vocabulary, splits, manifest."""
    source_csv = source_csv or DEFAULT_SOURCE_CSV
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    if not source_csv.is_file():
        raise FileNotFoundError(f"Source CSV not found: {source_csv}")

    rows = _read_csv(source_csv)
    examples = curate_examples(rows)
    all_texts = [e.text for e in examples]

    vocab = build_vocabulary(all_texts)
    save_vocabulary(vocab, output_dir / "itsm_vocabulary.json")

    hierarchy_path = output_dir / "label_hierarchy.json"
    hierarchy_path.write_text(json.dumps(LABEL_HIERARCHY, indent=2), encoding="utf-8")

    mapping_path = output_dir / "label_mapping.json"
    mapping_path.write_text(
        json.dumps(LABEL_HIERARCHY["mappings"], indent=2), encoding="utf-8"
    )

    splits = stratified_split(examples, seed=seed)
    _write_jsonl(output_dir / "labeled_all.jsonl", examples)
    _write_jsonl(output_dir / "train.jsonl", splits["train"])
    _write_jsonl(output_dir / "validation.jsonl", splits["validation"])
    _write_jsonl(output_dir / "test.jsonl", splits["test"])

    tc_count = sum(1 for e in examples if e.granularity == "test_case")
    step_count = sum(1 for e in examples if e.granularity == "step")

    manifest = {
        "version": "1.0",
        "source_csv": str(source_csv),
        "output_dir": str(output_dir),
        "random_seed": seed,
        "split_ratios": {"train": 0.70, "validation": 0.15, "test": 0.15},
        "counts": {
            "unique_test_cases": tc_count,
            "step_examples": step_count,
            "total_labeled_examples": len(examples),
            "train": len(splits["train"]),
            "validation": len(splits["validation"]),
            "test": len(splits["test"]),
        },
        "meets_minimum_2000": len(examples) >= MIN_LABELED_EXAMPLES,
        "label_distribution": _label_distribution(examples),
        "files": {
            "labeled_all": "labeled_all.jsonl",
            "train": "train.jsonl",
            "validation": "validation.jsonl",
            "test": "test.jsonl",
            "label_hierarchy": "label_hierarchy.json",
            "label_mapping": "label_mapping.json",
            "itsm_vocabulary": "itsm_vocabulary.json",
        },
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return manifest


def _label_distribution(examples: list[LabeledExample]) -> dict[str, dict[str, int]]:
    dist: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for ex in examples:
        if ex.granularity != "test_case":
            continue
        for dim, label in ex.labels.items():
            dist[dim][label] += 1
    return {dim: dict(counts) for dim, counts in dist.items()}


def load_jsonl_split(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)
