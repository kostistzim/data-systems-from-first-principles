import os
import shutil

from mlstore_lite.ai import FeatureServer, InferenceService, PredictionLog, PurchaseIntentModel
from mlstore_lite.catalog import default_feature_registry
from mlstore_lite.integration import create_mlstore_lite_system
from mlstore_lite.lineage import LineageLog
from mlstore_lite.quality import validate_events, write_quality_report


BASE_DIR = "demo_data/week12/metadata_lineage_quality"
PREDICTION_LOG_PATH = os.path.join(BASE_DIR, "predictions.jsonl")
LINEAGE_LOG_PATH = os.path.join(BASE_DIR, "lineage.jsonl")
QUALITY_REPORT_PATH = os.path.join(BASE_DIR, "quality_report.json")


def make_events() -> list[dict]:
    return [
        {"user_id": "0", "event_type": "click"},
        {"user_id": "0", "event_type": "purchase", "amount": 18.0},
        {"user_id": "1", "event_type": "click"},
        {"user_id": "", "event_type": "click"},
        {"user_id": "2", "event_type": "purchase", "amount": -3.0},
    ]


def run_week12_demo() -> dict:
    reset_demo_dir()
    registry = default_feature_registry()
    quality_report = validate_events(make_events())
    write_quality_report(QUALITY_REPORT_PATH, quality_report)

    system = create_mlstore_lite_system(BASE_DIR)
    batch_outputs = system.run_batch_features(quality_report.valid_events)

    prediction_log = PredictionLog(PREDICTION_LOG_PATH)
    lineage_log = LineageLog(LINEAGE_LOG_PATH)
    inference = InferenceService(
        feature_server=FeatureServer(system),
        model=PurchaseIntentModel(),
        prediction_log=prediction_log,
        lineage_log=lineage_log,
    )
    prediction = inference.predict_user("0")

    return {
        "registered_feature_count": len(registry),
        "batch_feature_count": len(batch_outputs),
        "quality_valid_count": quality_report.valid_count,
        "quality_invalid_count": quality_report.invalid_count,
        "lineage_record_count": len(lineage_log.read_all()),
        "prediction_label": prediction["label"],
        "prediction_probability": prediction["purchase_probability"],
        "quality_report_path": QUALITY_REPORT_PATH,
        "lineage_log_path": LINEAGE_LOG_PATH,
        "prediction_log_path": PREDICTION_LOG_PATH,
        "base_dir": BASE_DIR,
    }


def reset_demo_dir() -> None:
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)


def format_summary(result: dict) -> str:
    return "\n".join(
        [
            "=== WEEK 12 METADATA, LINEAGE, AND QUALITY DEMO ===",
            f"registered_features={result['registered_feature_count']}",
            f"quality_valid={result['quality_valid_count']}",
            f"quality_invalid={result['quality_invalid_count']}",
            f"batch_features_written={result['batch_feature_count']}",
            f"lineage_records={result['lineage_record_count']}",
            f"prediction_probability={result['prediction_probability']:.4f}",
            f"prediction_label={result['prediction_label']}",
            "",
            "Generated output:",
            f"base_dir={result['base_dir']}",
            f"quality_report={result['quality_report_path']}",
            f"lineage_log={result['lineage_log_path']}",
            f"prediction_log={result['prediction_log_path']}",
        ]
    )


def main() -> None:
    print(format_summary(run_week12_demo()))


if __name__ == "__main__":
    main()
