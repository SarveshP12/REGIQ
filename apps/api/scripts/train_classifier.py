import json
import os
from pathlib import Path

import mlflow
import mlflow.pytorch

DATASET_DIR = Path(__file__).resolve().parents[1] / "data" / "datasets" / "tcc_v1"


def fetch_training_data(split: str = "train") -> list[dict]:
    """Load curated labeled examples from prepared JSONL splits."""
    path = DATASET_DIR / f"{split}.jsonl"
    if not path.is_file():
        raise FileNotFoundError(
            f"Training split not found at {path}. "
            "Run: python scripts/prepare_training_dataset.py"
        )
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    print(f"Loaded {len(records)} examples from {path}")
    return records

def train_model():
    """Mock fine-tuning of BERT model with MLflow tracking"""
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment("regiq_tcc_classifier")
    
    with mlflow.start_run(run_name="weekly_retraining"):
        print("Starting model fine-tuning...")
        # tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        # model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=6)
        
        # Log params
        mlflow.log_param("epochs", 3)
        mlflow.log_param("batch_size", 16)
        mlflow.log_param("learning_rate", 2e-5)
        
        # Mock Training Loop
        print("Training model on mock data...")
        mlflow.log_metric("train_loss", 0.35, step=1)
        mlflow.log_metric("val_accuracy", 0.89, step=1)
        
        # Log model
        # mlflow.pytorch.log_model(model, "model")
        print("Model training complete and logged to MLflow.")

if __name__ == "__main__":
    train_model()
