import os
import shutil

from mlstore_lite.integration import create_mlstore_lite_system
from mlstore_lite.observability import ExperimentLog, get_logger, timed
from mlstore_lite.observability.logging import log_event


BASE_DIR = "demo_data/week8/evaluation"
RESULTS_PATH = os.path.join(BASE_DIR, "results.jsonl")


def reset_demo_dir() -> None:
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)


def make_batch_events(count: int) -> list[dict]:
    events = []
    for i in range(count):
        user_id = str(i % 25)
        if i % 5 == 0:
            events.append({"user_id": user_id, "event_type": "purchase", "amount": 10.0})
        else:
            events.append({"user_id": user_id, "event_type": "click"})
    return events


def make_stream_events(count: int) -> list[dict]:
    events = []
    for i in range(count):
        user_id = str(i % 25)
        if i % 7 == 0:
            events.append(
                {
                    "user_id": user_id,
                    "event_type": "purchase",
                    "amount": 5.0,
                    "timestamp": i,
                }
            )
        else:
            events.append({"user_id": user_id, "event_type": "click", "timestamp": i})
    return events


def record_timing(experiment_log: ExperimentLog, result, parameters: dict) -> None:
    experiment_log.record(
        experiment=result.label,
        metric="elapsed_time",
        value=result.elapsed_sec,
        unit="seconds",
        parameters=parameters,
    )

    output_size = result_size(result.result)
    experiment_log.record(
        experiment=result.label,
        metric="output_items",
        value=output_size,
        unit="count",
        parameters=parameters,
    )


def result_size(result) -> int:
    if isinstance(result, dict):
        return len(result)
    if isinstance(result, list):
        return len(result)
    return 1


def main() -> None:
    reset_demo_dir()
    logger = get_logger("mlstore_lite.week8")
    experiment_log = ExperimentLog(RESULTS_PATH)
    system = create_mlstore_lite_system(BASE_DIR)

    batch_events = make_batch_events(250)
    stream_events = make_stream_events(250)

    log_event(
        logger,
        "week8_evaluation_started",
        batch_events=len(batch_events),
        stream_events=len(stream_events),
        results_path=RESULTS_PATH,
    )

    measurements = [
        timed("batch_feature_runtime", lambda: system.run_batch_features(batch_events)),
        timed("stream_produce_runtime", lambda: system.produce_events(stream_events)),
        timed("stream_process_runtime", lambda: system.process_stream_events(max_records=500)),
        timed("feature_read_latency", lambda: system.get_feature("feature:user:0:event_count")),
    ]

    parameters = {
        "batch_events": len(batch_events),
        "stream_events": len(stream_events),
        "shards": 2,
        "replication_factor": 3,
    }

    for measurement in measurements:
        record_timing(experiment_log, measurement, parameters)
        log_event(
            logger,
            "measurement_recorded",
            experiment=measurement.label,
            elapsed_sec=measurement.elapsed_sec,
            output_items=result_size(measurement.result),
        )

    distribution = system.status()["key_distribution"]
    for shard_id, key_count in distribution.items():
        experiment_log.record(
            experiment="shard_distribution",
            metric=shard_id,
            value=key_count,
            unit="keys",
            parameters=parameters,
        )

    print("\n=== WEEK 8 EVALUATION SUMMARY ===")
    for measurement in measurements:
        print(
            f"{measurement.label}: "
            f"{measurement.elapsed_sec:.6f}s, "
            f"items={result_size(measurement.result)}"
        )

    print("\nShard distribution:")
    print(distribution)

    print("\nExperiment log:")
    print(RESULTS_PATH)

    log_event(logger, "week8_evaluation_finished", records=len(experiment_log.read_all()))


if __name__ == "__main__":
    main()
