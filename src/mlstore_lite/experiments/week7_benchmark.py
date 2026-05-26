import os
import shutil
import time

from mlstore_lite.integration import create_mlstore_lite_system


BASE_DIR = "demo_data/week7/benchmark"


def reset_demo_dir() -> None:
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)


def timed(label: str, fn) -> tuple[str, float, object]:
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    return label, elapsed, result


def make_batch_events(count: int) -> list[dict]:
    events = []
    for i in range(count):
        user_id = str(i % 20)
        if i % 5 == 0:
            events.append({"user_id": user_id, "event_type": "purchase", "amount": 10.0})
        else:
            events.append({"user_id": user_id, "event_type": "click"})
    return events


def make_stream_events(count: int) -> list[dict]:
    events = []
    for i in range(count):
        user_id = str(i % 20)
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


def main() -> None:
    reset_demo_dir()
    system = create_mlstore_lite_system(BASE_DIR)

    batch_events = make_batch_events(200)
    stream_events = make_stream_events(200)

    measurements = [
        timed("batch feature job (200 events)", lambda: system.run_batch_features(batch_events)),
        timed("produce stream events (200 events)", lambda: system.produce_events(stream_events)),
        timed("process stream events (200 events)", lambda: system.process_stream_events(max_records=500)),
        timed("read sample feature", lambda: system.get_feature("feature:user:0:event_count")),
    ]

    print("\n=== WEEK 7 BASIC BENCHMARK ===")
    for label, elapsed, result in measurements:
        if isinstance(result, dict):
            result_size = len(result)
        elif isinstance(result, list):
            result_size = len(result)
        else:
            result_size = 1
        print(f"{label}: {elapsed:.6f}s, result items: {result_size}")

    print("\nFinal distribution:")
    print(system.status()["key_distribution"])


if __name__ == "__main__":
    main()
