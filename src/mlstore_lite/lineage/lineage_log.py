import json
import os
from datetime import datetime, timezone
from typing import Optional


class LineageLog:
    """
    Local JSON-lines log for feature and prediction traceability.
    """

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(self.path, "a", encoding="utf-8").close()

    def record(self, record_type: str, payload: dict) -> dict:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "record_type": record_type,
            **payload,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True))
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        return record

    def record_prediction(
        self,
        user_id: str,
        model_version: str,
        input_feature_keys: list[str],
        output_keys: list[str],
        missing_features: Optional[list[str]] = None,
        extra: Optional[dict] = None,
    ) -> dict:
        payload = {
            "user_id": str(user_id),
            "model_version": model_version,
            "input_feature_keys": input_feature_keys,
            "output_keys": output_keys,
            "missing_features": missing_features or [],
        }
        if extra:
            payload.update(extra)
        return self.record("prediction_lineage", payload)

    def read_all(self) -> list[dict]:
        records = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
