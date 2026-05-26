import os
import shutil

from mlstore_lite.integration import create_mlstore_lite_system


BASE_DIR = "demo_data/week7/integration"


def reset_demo_dir() -> None:
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)


def main() -> None:
    reset_demo_dir()
    system = create_mlstore_lite_system(BASE_DIR)

    batch_events = [
        {"user_id": "42", "event_type": "click"},
        {"user_id": "42", "event_type": "purchase", "amount": 10.0},
        {"user_id": "7", "event_type": "click"},
    ]
    stream_events = [
        {"user_id": "42", "event_type": "click", "timestamp": 10},
        {"user_id": "42", "event_type": "click", "timestamp": 20},
        {"user_id": "7", "event_type": "purchase", "amount": 5.0, "timestamp": 70},
    ]

    print("\n=== WEEK 7 INTEGRATION DEMO ===")

    print("\nRunning batch feature job:")
    batch_outputs = system.run_batch_features(batch_events)
    for key in sorted(batch_outputs):
        print(f"{key} = {system.get_feature(key)}")

    print("\nProducing stream events:")
    for event, offset in zip(stream_events, system.produce_events(stream_events)):
        print(f"offset {offset}: {event}")

    print("\nProcessing stream events:")
    stream_outputs = system.process_stream_events(max_records=10)
    for key in sorted(stream_outputs):
        print(f"{key} = {system.get_feature(key)}")

    print("\nManual failover on shard-a:")
    new_leader = system.failover_shard("shard-a")
    print(f"new shard-a leader: {new_leader}")

    print("\nWriting after failover:")
    system.produce_event({"user_id": "42", "event_type": "purchase", "amount": 3.0, "timestamp": 80})
    more_outputs = system.process_stream_events(max_records=10)
    for key in sorted(more_outputs):
        print(f"{key} = {system.get_feature(key)}")

    print("\nFinal system status:")
    print(system.status())


if __name__ == "__main__":
    main()
