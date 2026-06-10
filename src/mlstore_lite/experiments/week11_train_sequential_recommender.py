import json
import os
import shutil

from mlstore_lite.ai import TinyAttentionRecommender
from mlstore_lite.observability import ExperimentLog, timed
from mlstore_lite.quality import validate_events, write_quality_report
from mlstore_lite.training import Vocabulary, build_sequence_examples, load_events_or_sample


DATASET_PATH = "data/raw/retailrocket/events.csv"
BASE_DIR = "demo_data/week11"
ARTIFACT_DIR = "model_artifacts/week11"
MODEL_PATH = os.path.join(ARTIFACT_DIR, "tiny_attention_recommender.json")
VOCAB_PATH = os.path.join(ARTIFACT_DIR, "vocabulary.json")
METRICS_PATH = os.path.join(BASE_DIR, "training_metrics.json")
QUALITY_REPORT_PATH = os.path.join(BASE_DIR, "training_quality_report.json")
EXPERIMENT_LOG_PATH = os.path.join(BASE_DIR, "experiments.jsonl")


def train_week11_model(
    dataset_path: str = DATASET_PATH,
    max_rows: int | None = 50000,
    reset_outputs: bool = True,
) -> dict:
    if reset_outputs:
        reset_demo_outputs()

    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    events, source = load_events_or_sample(dataset_path, max_rows=max_rows)
    quality_report = validate_events(
        [
            {
                "user_id": event.user_id,
                "event_type": event.event_type,
                "item_id": event.item_id,
                "timestamp": event.timestamp,
            }
            for event in events
        ],
        require_timestamp=True,
    )
    write_quality_report(QUALITY_REPORT_PATH, quality_report)
    examples = build_sequence_examples(events, max_history_events=10)
    if len(examples) < 2:
        raise ValueError("Need at least two sequence examples to train Week 11 model")

    vocabulary = Vocabulary.build([example.input_tokens for example in examples])
    train_examples, test_examples = deterministic_stratified_split(
        examples,
        test_ratio=0.3,
    )
    model = TinyAttentionRecommender(max_sequence_length=20, embedding_dim=16)

    timed_training = timed(
        "week11_train_sequential_recommender",
        lambda: model.fit(train_examples, vocabulary),
    )
    train_metrics = timed_training.result
    test_metrics = model.evaluate(test_examples, vocabulary)

    model.save(MODEL_PATH)
    vocabulary.save(VOCAB_PATH)

    result = {
        "dataset_source": source,
        "event_count": len(events),
        "quality_valid_count": quality_report.valid_count,
        "quality_invalid_count": quality_report.invalid_count,
        "example_count": len(examples),
        "train_examples": len(train_examples),
        "test_examples": len(test_examples),
        "vocabulary_size": len(vocabulary),
        "training_seconds": round(timed_training.elapsed_sec, 6),
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "model_path": MODEL_PATH,
        "vocabulary_path": VOCAB_PATH,
        "quality_report_path": QUALITY_REPORT_PATH,
    }
    write_json(METRICS_PATH, result)
    record_experiment_log(result)
    return result


def deterministic_stratified_split(examples: list, test_ratio: float) -> tuple[list, list]:
    """
    Keep both purchase and non-purchase examples in the tiny sample holdout.

    A strict time split is usually better for real recommendation work, but the
    built-in sample is very small and would otherwise create an unhelpful test
    set with almost only one class.
    """
    positives = [example for example in examples if example.label == 1]
    negatives = [example for example in examples if example.label == 0]

    train_examples = []
    test_examples = []
    for group in [positives, negatives]:
        group = sorted(group, key=lambda item: (item.user_id, item.timestamp))
        test_count = max(1, int(len(group) * test_ratio)) if len(group) > 1 else 0
        test_examples.extend(group[:test_count])
        train_examples.extend(group[test_count:])

    return train_examples, test_examples


def reset_demo_outputs() -> None:
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)


def write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def record_experiment_log(result: dict) -> None:
    log = ExperimentLog(EXPERIMENT_LOG_PATH)
    parameters = {
        "dataset_source": result["dataset_source"],
        "event_count": result["event_count"],
        "example_count": result["example_count"],
        "vocabulary_size": result["vocabulary_size"],
    }
    log.record("week11_sequential_recommender", "training_seconds", result["training_seconds"], "seconds", parameters)
    for metric, value in result["test_metrics"].items():
        if metric != "confusion_matrix":
            log.record("week11_sequential_recommender", f"test_{metric}", value, "score", parameters)


def format_summary(result: dict) -> str:
    return "\n".join(
        [
            "=== WEEK 11 SEQUENTIAL RECOMMENDER TRAINING ===",
            f"dataset_source={result['dataset_source']}",
            f"events={result['event_count']}",
            f"quality_valid={result['quality_valid_count']}",
            f"quality_invalid={result['quality_invalid_count']}",
            f"examples={result['example_count']}",
            f"vocabulary_size={result['vocabulary_size']}",
            f"training_seconds={result['training_seconds']}",
            "",
            "Test metrics:",
            f"accuracy={result['test_metrics']['accuracy']}",
            f"precision={result['test_metrics']['precision']}",
            f"recall={result['test_metrics']['recall']}",
            f"f1={result['test_metrics']['f1']}",
            f"confusion_matrix={result['test_metrics']['confusion_matrix']}",
            "",
            "Saved files:",
            f"model={result['model_path']}",
            f"vocabulary={result['vocabulary_path']}",
            f"metrics={METRICS_PATH}",
            f"quality_report={result['quality_report_path']}",
        ]
    )


def main() -> None:
    result = train_week11_model()
    print(format_summary(result))


if __name__ == "__main__":
    main()
