import os
import shutil

from mlstore_lite.ai import PredictionLog, SequentialInferenceService, TinyAttentionRecommender
from mlstore_lite.ai.audit import summarize_predictions
from mlstore_lite.experiments.week11_train_sequential_recommender import (
    MODEL_PATH,
    VOCAB_PATH,
    train_week11_model,
)
from mlstore_lite.integration import create_mlstore_lite_system
from mlstore_lite.lineage import LineageLog
from mlstore_lite.quality import validate_events, write_quality_report
from mlstore_lite.training import Vocabulary, build_user_histories, load_events_or_sample, to_batch_events


BASE_DIR = "demo_data/week11/recommender_demo"
PREDICTION_LOG_PATH = os.path.join(BASE_DIR, "predictions.jsonl")
LINEAGE_LOG_PATH = os.path.join(BASE_DIR, "lineage.jsonl")
QUALITY_REPORT_PATH = os.path.join(BASE_DIR, "quality_report.json")


def run_week11_recommender_demo() -> dict:
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VOCAB_PATH):
        train_week11_model(reset_outputs=True)

    reset_demo_dir()
    events, source = load_events_or_sample()
    histories = build_user_histories(events)
    system = create_mlstore_lite_system(BASE_DIR)
    batch_quality = validate_events(to_batch_events(events))
    write_quality_report(QUALITY_REPORT_PATH, batch_quality)
    system.run_batch_features(batch_quality.valid_events)

    model = TinyAttentionRecommender.load(MODEL_PATH)
    vocabulary = Vocabulary.load(VOCAB_PATH)
    inference = SequentialInferenceService(model, vocabulary)
    prediction_log = PredictionLog(PREDICTION_LOG_PATH)
    lineage_log = LineageLog(LINEAGE_LOG_PATH)

    user_ids = sorted(histories.keys())[:4] + ["999"]
    predictions = []
    for user_id in user_ids:
        user_events = histories.get(user_id, [])
        prediction = inference.predict_from_events(user_id, user_events)
        prediction_log.record(prediction)
        output_keys = write_prediction_to_store(system, prediction)
        lineage_log.record_prediction(
            user_id=user_id,
            model_version=prediction["model_version"],
            input_feature_keys=[],
            output_keys=output_keys,
            extra={
                "input_event_count": len(user_events),
                "input_token_count": prediction["sequence_length"],
                "label": prediction["label"],
                "confidence": prediction["confidence"],
            },
        )
        predictions.append(prediction)

    audit = summarize_predictions(predictions)
    status = system.status()
    return {
        "dataset_source": source,
        "prediction_count": len(predictions),
        "predictions": predictions,
        "audit": audit,
        "quality_valid_count": batch_quality.valid_count,
        "quality_invalid_count": batch_quality.invalid_count,
        "shard_distribution": status["key_distribution"],
        "prediction_log_path": PREDICTION_LOG_PATH,
        "lineage_log_path": LINEAGE_LOG_PATH,
        "quality_report_path": QUALITY_REPORT_PATH,
        "base_dir": BASE_DIR,
    }


def write_prediction_to_store(system, prediction: dict) -> list[str]:
    user_id = prediction["user_id"]
    probability_key = f"prediction:user:{user_id}:purchase_probability"
    label_key = f"prediction:user:{user_id}:label"
    system.store.put(probability_key, str(prediction["purchase_probability"]))
    system.store.put(label_key, prediction["label"])
    return [probability_key, label_key]


def reset_demo_dir() -> None:
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)


def format_summary(result: dict) -> str:
    lines = [
        "=== WEEK 11 SEQUENTIAL RECOMMENDER DEMO ===",
        f"dataset_source={result['dataset_source']}",
        f"prediction_count={result['prediction_count']}",
        f"quality_valid={result['quality_valid_count']}",
        f"quality_invalid={result['quality_invalid_count']}",
        f"shard_distribution={result['shard_distribution']}",
        "",
        "Predictions:",
    ]
    for prediction in result["predictions"]:
        top_tokens = [item["token"] for item in prediction["important_tokens"][:3]]
        lines.append(
            f"user={prediction['user_id']} "
            f"probability={prediction['purchase_probability']:.4f} "
            f"confidence={prediction['confidence']:.4f} "
            f"label={prediction['label']} "
            f"top_attention={top_tokens}"
        )

    lines.extend(
        [
            "",
            "Audit:",
            str(result["audit"]),
            "",
            "Generated output:",
            f"base_dir={result['base_dir']}",
            f"prediction_log={result['prediction_log_path']}",
            f"lineage_log={result['lineage_log_path']}",
            f"quality_report={result['quality_report_path']}",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    print(format_summary(run_week11_recommender_demo()))


if __name__ == "__main__":
    main()
