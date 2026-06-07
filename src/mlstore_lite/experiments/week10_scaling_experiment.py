import os
import shutil

from mlstore_lite.integration import create_mlstore_lite_system
from mlstore_lite.observability import ExperimentLog, timed


BASE_DIR = "demo_data/week10/scaling"
RESULTS_PATH = os.path.join(BASE_DIR, "results.jsonl")
WORKLOAD_SIZES = [250, 1000, 2500]


def reset_demo_dir() -> None:
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)


def make_batch_events(count: int) -> list[dict]:
    events = []
    for i in range(count):
        user_id = str(i % max(25, count // 20))
        if i % 5 == 0:
            events.append({"user_id": user_id, "event_type": "purchase", "amount": 10.0})
        else:
            events.append({"user_id": user_id, "event_type": "click"})
    return events


def make_stream_events(count: int) -> list[dict]:
    events = []
    for i in range(count):
        user_id = str(i % max(25, count // 20))
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


def record_measurement(
    experiment_log: ExperimentLog,
    workload_size: int,
    metric: str,
    value,
    unit: str,
) -> None:
    experiment_log.record(
        experiment="week10_workload_scaling",
        metric=metric,
        value=value,
        unit=unit,
        parameters={
            "batch_events": workload_size,
            "stream_events": workload_size,
            "shards": 2,
            "replication_factor": 3,
        },
    )


def run_workload(workload_size: int, experiment_log: ExperimentLog) -> dict:
    workload_dir = os.path.join(BASE_DIR, f"workload-{workload_size}")
    system = create_mlstore_lite_system(workload_dir)
    batch_events = make_batch_events(workload_size)
    stream_events = make_stream_events(workload_size)

    batch_result = timed(
        "batch_runtime",
        lambda: system.run_batch_features(batch_events),
    )
    produce_result = timed(
        "stream_produce_runtime",
        lambda: system.produce_events(stream_events),
    )
    process_result = timed(
        "stream_process_runtime",
        lambda: system.process_stream_events(max_records=workload_size * 2),
    )
    read_result = timed(
        "feature_read_latency",
        lambda: system.get_feature("feature:user:0:event_count"),
    )

    distribution = system.status()["key_distribution"]
    total_keys = sum(distribution.values())

    for result in [batch_result, produce_result, process_result, read_result]:
        record_measurement(
            experiment_log,
            workload_size,
            result.label,
            result.elapsed_sec,
            "seconds",
        )

    record_measurement(experiment_log, workload_size, "total_feature_keys", total_keys, "keys")
    for shard_id, key_count in distribution.items():
        record_measurement(
            experiment_log,
            workload_size,
            f"keys_on_{shard_id}",
            key_count,
            "keys",
        )

    return {
        "workload_size": workload_size,
        "batch_runtime": batch_result.elapsed_sec,
        "stream_produce_runtime": produce_result.elapsed_sec,
        "stream_process_runtime": process_result.elapsed_sec,
        "feature_read_latency": read_result.elapsed_sec,
        "total_feature_keys": total_keys,
        "shard_distribution": distribution,
    }


def main() -> None:
    reset_demo_dir()
    experiment_log = ExperimentLog(RESULTS_PATH)
    summaries = [
        run_workload(workload_size, experiment_log)
        for workload_size in WORKLOAD_SIZES
    ]

    print("\n=== WEEK 10 WORKLOAD SCALING EXPERIMENT ===")
    print("events | batch_s | produce_s | process_s | read_s | keys | distribution")
    for summary in summaries:
        print(
            f"{summary['workload_size']:>6} | "
            f"{summary['batch_runtime']:.6f} | "
            f"{summary['stream_produce_runtime']:.6f} | "
            f"{summary['stream_process_runtime']:.6f} | "
            f"{summary['feature_read_latency']:.6f} | "
            f"{summary['total_feature_keys']:>4} | "
            f"{summary['shard_distribution']}"
        )

    print("\nExperiment log:")
    print(RESULTS_PATH)


if __name__ == "__main__":
    main()
