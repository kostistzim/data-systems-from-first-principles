import os
import shutil

from mlstore_lite.ai import (
    FeatureServer,
    InferenceService,
    PredictionLog,
    PurchaseIntentModel,
)
from mlstore_lite.integration import create_mlstore_lite_system
from mlstore_lite.lineage import LineageLog
from mlstore_lite.quality import QualityReport, validate_events, write_quality_report


BASE_DIR = "demo_data/week9/ai"
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


def main() -> None:
    reset_demo_dir()
    system = create_mlstore_lite_system(BASE_DIR)
    batch_quality = validate_events(make_batch_events())
    stream_quality = validate_events(make_stream_events(), require_timestamp=True)
    write_quality_report(
        QUALITY_REPORT_PATH,
        QualityReport(
            valid_events=batch_quality.valid_events + stream_quality.valid_events,
            issues=batch_quality.issues + stream_quality.issues,
        ),
    )

    system.run_batch_features(batch_quality.valid_events)
    system.produce_events(stream_quality.valid_events)
    system.process_stream_events(max_records=100)

    feature_server = FeatureServer(
        system=system,
        recent_window_starts=RECENT_WINDOW_STARTS,
    )
    model = PurchaseIntentModel()
    prediction_log = PredictionLog(PREDICTION_LOG_PATH)
    lineage_log = LineageLog(LINEAGE_LOG_PATH)
    inference_service = InferenceService(
        feature_server=feature_server,
        model=model,
        prediction_log=prediction_log,
        lineage_log=lineage_log,
    )

    print("\n=== WEEK 9 AI INFERENCE DEMO ===")
    print(
        f"quality_valid={batch_quality.valid_count + stream_quality.valid_count} "
        f"quality_invalid={batch_quality.invalid_count + stream_quality.invalid_count}"
    )
    for user_id in ["0", "1", "2", "999"]:
        prediction = inference_service.predict_user(user_id)
        print(
            f"user={prediction['user_id']} "
            f"probability={prediction['purchase_probability']:.4f} "
            f"confidence={prediction['confidence']:.4f} "
            f"label={prediction['label']} "
            f"warnings={prediction['warnings']}"
        )

    print("\nPrediction log:")
    print(PREDICTION_LOG_PATH)
    print("Lineage log:")
    print(LINEAGE_LOG_PATH)
    print("Quality report:")
    print(QUALITY_REPORT_PATH)


if __name__ == "__main__":
    main()
