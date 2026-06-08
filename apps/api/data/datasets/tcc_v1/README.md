# TCC Classifier Training Dataset (v1)

Generated from `docs/sample_data/Combined_500_ITSM_Test_Cases.csv`.

## Regenerate

```bash
cd apps/api
python scripts/prepare_training_dataset.py
```

## Artifacts

| File | Description |
|------|-------------|
| `manifest.json` | Counts, split ratios, label distribution |
| `label_hierarchy.json` | Canonical labels + ServiceNow module tree |
| `label_mapping.json` | CSV column → classifier label maps |
| `itsm_vocabulary.json` | Tables, modules, terms, abbreviations |
| `labeled_all.jsonl` | All curated examples |
| `train.jsonl` | 70% split (test-case stratified; steps follow parent) |
| `validation.jsonl` | 15% split |
| `test.jsonl` | 15% split |

Each JSONL record includes `text`, six `labels` (TCC dimensions), and `metadata`.
