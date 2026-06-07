import os
import shutil

from mlstore_lite.integration import create_mlstore_lite_system
from mlstore_lite.observability import ExperimentLog, timed
from mlstore_lite.stream.processor import feature_key
from mlstore_lite.stream.windows import TumblingWindow


BASE_DIR = "demo_data/week10/hotspot"
RESULTS_PATH = os.path.join(BASE_DIR, "results.jsonl")
EVENT_COUNT = 1000


def reset_demo_dir() -> None:
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)


def make_balanced_events(count: int) -> list[dict]:
    return [
        {"user_id": str(i % 100), "event_type": "click", "timestamp": i}
        for i in range(count)
    ]


def make_hotspot_events(count: int) -> list[dict]:
    events = []
    for i in range(count):
        if i % 10 < 8:
            user_id = "hot-user"
        else:
            user_id = str(i % 100)
        events.append({"user_id": user_id, "event_type": "click", "timestamp": i})
    return events


def record(
    experiment_log: ExperimentLog,
    workload_name: str,
    metric: str,
    value,
    unit: str,
) -> None:
    experiment_log.record(
        experiment="week10_shard_hotspot",
        metric=metric,
        value=value,
        unit=unit,
        parameters={
            "workload": workload_name,
            "events": EVENT_COUNT,
            "shards": 2,
            "replication_factor": 3,
        },
    )


def run_workload(
    workload_name: str,
    events: list[dict],
    experiment_log: ExperimentLog,
) -> dict:
    workload_dir = os.path.join(BASE_DIR, workload_name)
    system = create_mlstore_lite_system(workload_dir)
    event_pressure = event_pressure_by_shard(system, events)

    produce_result = timed("stream_produce_runtime", lambda: system.produce_events(events))
    process_result = timed(
        "stream_process_runtime",
        lambda: system.process_stream_events(max_records=len(events) * 2),
    )

    distribution = system.status()["key_distribution"]
    request_counts = system.store.request_counts()
    hotspot_report = system.store.hotspot_report()
    hottest_shard = hotspot_report[0]

    record(experiment_log, workload_name, "stream_produce_runtime", produce_result.elapsed_sec, "seconds")
    record(experiment_log, workload_name, "stream_process_runtime", process_result.elapsed_sec, "seconds")
    record(experiment_log, workload_name, "hottest_shard_requests", hottest_shard["requests"], "requests")

    for shard_id, event_count in event_pressure.items():
        record(experiment_log, workload_name, f"events_routed_to_{shard_id}", event_count, "events")

    for shard_id, key_count in distribution.items():
        record(experiment_log, workload_name, f"keys_on_{shard_id}", key_count, "keys")

    for shard_id, request_count in request_counts.items():
        record(experiment_log, workload_name, f"requests_on_{shard_id}", request_count, "requests")

    return {
        "workload": workload_name,
        "produce_runtime": produce_result.elapsed_sec,
        "process_runtime": process_result.elapsed_sec,
        "key_distribution": distribution,
        "request_counts": request_counts,
        "event_pressure": event_pressure,
        "hottest_shard": hottest_shard,
    }


def event_pressure_by_shard(system, events: list[dict]) -> dict:
    window = TumblingWindow(60)
    pressure = {shard_id: 0 for shard_id in system.store.shard_groups}

    for event in events:
        user_id = str(event["user_id"])
        window_start = window.start_for(int(event["timestamp"]))
        key = feature_key(user_id, window_start, "event_count")
        shard_id = system.store.get_shard_id(key)
        pressure[shard_id] += 1

    return pressure


def main() -> None:
    reset_demo_dir()
    experiment_log = ExperimentLog(RESULTS_PATH)
    summaries = [
        run_workload("balanced", make_balanced_events(EVENT_COUNT), experiment_log),
        run_workload("hotspot", make_hotspot_events(EVENT_COUNT), experiment_log),
    ]

    print("\n=== WEEK 10 SHARD HOTSPOT EXPERIMENT ===")
    for summary in summaries:
        print(f"\nWorkload: {summary['workload']}")
        print(f"produce_s={summary['produce_runtime']:.6f}")
        print(f"process_s={summary['process_runtime']:.6f}")
        print(f"event_pressure={summary['event_pressure']}")
        print(f"key_distribution={summary['key_distribution']}")
        print(f"request_counts={summary['request_counts']}")
        print(f"hottest_shard={summary['hottest_shard']}")

    print("\nExperiment log:")
    print(RESULTS_PATH)


if __name__ == "__main__":
    main()
