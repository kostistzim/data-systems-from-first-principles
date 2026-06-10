import os
import shutil

from mlstore_lite.ai import (
    FeatureServer,
    InferenceService,
    PredictionLog,
    PurchaseIntentModel,
)
from mlstore_lite.catalog import default_feature_registry
from mlstore_lite.integration import create_mlstore_lite_system
from mlstore_lite.lineage import LineageLog
from mlstore_lite.quality import QualityReport, validate_events, write_quality_report


BASE_DIR = "demo_data/final_demo"
PREDICTION_LOG_PATH = os.path.join(BASE_DIR, "predictions.jsonl")
LINEAGE_LOG_PATH = os.path.join(BASE_DIR, "lineage.jsonl")
QUALITY_REPORT_PATH = os.path.join(BASE_DIR, "quality_report.json")
RECENT_WINDOW_STARTS = [0, 60, 120, 180, 240]


def reset_demo_dir() -> None:
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)


def make_batch_events() -> list[dict]:
    events = []

    for _ in range(8):
        events.append({"user_id": "0", "event_type": "click"})
    for _ in range(3):
        events.append({"user_id": "0", "event_type": "purchase", "amount": 20.0})

    for _ in range(5):
        events.append({"user_id": "1", "event_type": "click"})
    events.append({"user_id": "1", "event_type": "purchase", "amount": 12.0})

    for _ in range(3):
        events.append({"user_id": "2", "event_type": "click"})

    return events


def make_stream_events() -> list[dict]:
    events = []

    for timestamp in [1, 15, 70, 130, 190]:
        events.append({"user_id": "0", "event_type": "click", "timestamp": timestamp})
    for timestamp in [75, 210]:
        events.append(
            {
                "user_id": "0",
                "event_type": "purchase",
                "amount": 10.0,
                "timestamp": timestamp,
            }
        )

    for timestamp in [5, 65, 125]:
        events.append({"user_id": "1", "event_type": "click", "timestamp": timestamp})

    return events


def run_final_demo() -> dict:
    reset_demo_dir()
    system = create_mlstore_lite_system(BASE_DIR)

    batch_events = make_batch_events()
    stream_events = make_stream_events()
    batch_quality = validate_events(batch_events)
    stream_quality = validate_events(stream_events, require_timestamp=True)
    write_quality_report(
        QUALITY_REPORT_PATH,
        merge_quality_reports(batch_quality, stream_quality),
    )

    batch_outputs = system.run_batch_features(batch_quality.valid_events)
    stream_offsets = system.produce_events(stream_quality.valid_events)
    stream_outputs = system.process_stream_events(max_records=100)
    registry = default_feature_registry()

    feature_server = FeatureServer(
        system=system,
        recent_window_starts=RECENT_WINDOW_STARTS,
    )
    prediction_log = PredictionLog(PREDICTION_LOG_PATH)
    lineage_log = LineageLog(LINEAGE_LOG_PATH)
    inference_service = InferenceService(
        feature_server=feature_server,
        model=PurchaseIntentModel(),
        prediction_log=prediction_log,
        lineage_log=lineage_log,
    )
    predictions = [
        inference_service.predict_user(user_id)
        for user_id in ["0", "1", "2", "999"]
    ]

    status = system.status()
    return {
        "batch_event_count": len(batch_events),
        "valid_batch_event_count": batch_quality.valid_count,
        "valid_stream_event_count": stream_quality.valid_count,
        "invalid_event_count": batch_quality.invalid_count + stream_quality.invalid_count,
        "batch_feature_count": len(batch_outputs),
        "stream_event_count": len(stream_events),
        "stream_offset_count": len(stream_offsets),
        "stream_feature_count": len(stream_outputs),
        "consumer_offset": status["consumer_offset"],
        "shard_distribution": status["key_distribution"],
        "prediction_count": len(predictions),
        "predictions": predictions,
        "prediction_log_path": PREDICTION_LOG_PATH,
        "lineage_log_path": LINEAGE_LOG_PATH,
        "quality_report_path": QUALITY_REPORT_PATH,
        "registered_feature_count": len(registry),
        "base_dir": BASE_DIR,
    }


def format_summary(result: dict) -> str:
    lines = [
        "=== MLSTORE-LITE FINAL DEMO ===",
        "",
        "Pipeline:",
        "events -> batch/stream features -> sharded replicated store -> inference",
        "",
        "Feature computation:",
        f"batch_events={result['batch_event_count']}",
        f"valid_batch_events={result['valid_batch_event_count']}",
        f"valid_stream_events={result['valid_stream_event_count']}",
        f"invalid_events={result['invalid_event_count']}",
        f"batch_features_written={result['batch_feature_count']}",
        f"stream_events={result['stream_event_count']}",
        f"stream_features_written={result['stream_feature_count']}",
        f"consumer_offset={result['consumer_offset']}",
        "",
        "Shard distribution:",
        str(result["shard_distribution"]),
        "",
        "Predictions:",
    ]

    for prediction in result["predictions"]:
        lines.append(
            f"user={prediction['user_id']} "
            f"probability={prediction['purchase_probability']:.4f} "
            f"confidence={prediction['confidence']:.4f} "
            f"label={prediction['label']} "
            f"warnings={prediction['warnings']}"
        )

    lines.extend(
        [
            "",
            "Generated output:",
            f"base_dir={result['base_dir']}",
            f"prediction_log={result['prediction_log_path']}",
            f"lineage_log={result['lineage_log_path']}",
            f"quality_report={result['quality_report_path']}",
            f"registered_features={result['registered_feature_count']}",
        ]
    )
    return "\n".join(lines)


def merge_quality_reports(batch_report, stream_report):
    return QualityReport(
        valid_events=batch_report.valid_events + stream_report.valid_events,
        issues=batch_report.issues + stream_report.issues,
    )


def main() -> None:
    print(format_summary(run_final_demo()))


if __name__ == "__main__":
    main()
