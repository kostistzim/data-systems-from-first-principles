import json
import os
from datetime import datetime, timezone


class PredictionLog:
    """
    Local JSON-lines log for model predictions.
    """

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(self.path, "a", encoding="utf-8").close()

    def record(self, prediction: dict) -> dict:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **prediction,
        }

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, sort_keys=True))
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

        return payload

    def read_all(self) -> list[dict]:
        records = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
