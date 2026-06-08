"""Tests for TCC training dataset preparation."""

import json
from pathlib import Path

import pytest

from app.core.ai.dataset.label_hierarchy import map_business_process
from app.core.ai.dataset.prepare import (
    DEFAULT_SOURCE_CSV,
    MIN_LABELED_EXAMPLES,
    curate_examples,
    prepare_dataset,
    stratified_split,
    _read_csv,
)


def test_source_csv_exists():
    assert DEFAULT_SOURCE_CSV.is_file(), f"Missing sample CSV: {DEFAULT_SOURCE_CSV}"


def test_map_business_process_incident():
    assert map_business_process("Incident Logging", "State: New") == "Incident Management"
    assert map_business_process("Change Enablement", "Change Management") == "Change Management"


def test_curate_meets_minimum_examples():
    rows = _read_csv(DEFAULT_SOURCE_CSV)
    examples = curate_examples(rows)
    assert len(examples) >= MIN_LABELED_EXAMPLES
    tc = [e for e in examples if e.granularity == "test_case"]
    steps = [e for e in examples if e.granularity == "step"]
    assert len(tc) == 500
    assert len(steps) == len(rows)


def test_split_ratios_sum_to_all_test_cases(tmp_path: Path):
    rows = _read_csv(DEFAULT_SOURCE_CSV)
    examples = curate_examples(rows)
    splits = stratified_split(examples, seed=42)
    tc_train = {e.id for e in splits["train"] if e.granularity == "test_case"}
    tc_val = {e.id for e in splits["validation"] if e.granularity == "test_case"}
    tc_test = {e.id for e in splits["test"] if e.granularity == "test_case"}
    all_tc = tc_train | tc_val | tc_test
    assert len(tc_train) + len(tc_val) + len(tc_test) == 500
    assert not (tc_train & tc_val)
    assert not (tc_train & tc_test)
    # ~70/15/15 with rounding
    assert 330 <= len(tc_train) <= 360
    assert 65 <= len(tc_val) <= 85
    assert 65 <= len(tc_test) <= 85


@pytest.mark.skipif(not DEFAULT_SOURCE_CSV.is_file(), reason="sample CSV not present")
def test_prepare_dataset_writes_artifacts(tmp_path: Path):
    out = tmp_path / "tcc_v1"
    manifest = prepare_dataset(source_csv=DEFAULT_SOURCE_CSV, output_dir=out, seed=42)
    assert manifest["meets_minimum_2000"]
    assert (out / "train.jsonl").is_file()
    assert (out / "itsm_vocabulary.json").is_file()
    assert (out / "label_hierarchy.json").is_file()
    vocab = json.loads((out / "itsm_vocabulary.json").read_text(encoding="utf-8"))
    assert "servicenow_tables" in vocab
    assert len(vocab["servicenow_tables"]) > 10
