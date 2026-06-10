import json
import os

from .validators import QualityReport


def write_quality_report(path: str, report: QualityReport) -> dict:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = report.to_dict()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    return payload
