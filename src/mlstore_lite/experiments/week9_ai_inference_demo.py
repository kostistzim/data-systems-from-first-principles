import os
import shutil

from mlstore_lite.ai import (
    FeatureServer,
    InferenceService,
    PredictionLog,
    PurchaseIntentModel,
)
from mlstore_lite.integration import create_mlstore_lite_system


BASE_DIR = "demo_data/week9/ai"
PREDICTION_LOG_PATH = os.path.join(BASE_DIR, "predictions.jsonl")
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

    system.run_batch_features(make_batch_events())
    system.produce_events(make_stream_events())
    system.process_stream_events(max_records=100)

    feature_server = FeatureServer(
        system=system,
        recent_window_starts=RECENT_WINDOW_STARTS,
    )
    model = PurchaseIntentModel()
    prediction_log = PredictionLog(PREDICTION_LOG_PATH)
    inference_service = InferenceService(
        feature_server=feature_server,
        model=model,
        prediction_log=prediction_log,
    )

    print("\n=== WEEK 9 AI INFERENCE DEMO ===")
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


if __name__ == "__main__":
    main()
