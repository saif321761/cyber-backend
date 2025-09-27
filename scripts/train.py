# scripts/train.py
"""
Run from project root:
python -m scripts.train path/to/historical_logs.jsonl
Each line should be a JSON log object (same schema as LogItem).
"""
import json
import sys
from pathlib import Path
from app.utils.preprocessing import batch_to_matrix
from app.services.detector import AnomalyDetector
from app.core import settings

def load_jsonl(p: Path):
    with p.open("r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.train <historical_logs.jsonl>")
        sys.exit(2)
    p = Path(sys.argv[1])
    if not p.exists():
        print("File not found:", p)
        sys.exit(2)
    logs = list(load_jsonl(p))
    if len(logs) < 10:
        print("Need more logs to train (>=10 recommended). Found:", len(logs))
        sys.exit(2)

    # Convert to feature matrix
    X = batch_to_matrix(logs)

    # Train Isolation Forest
    detector = AnomalyDetector()
    detector.fit(X)

    print(f"✅ Trained and saved model to: {settings.MODEL_PATH} and {settings.SCALER_PATH}")

if __name__ == "__main__":
    main()
