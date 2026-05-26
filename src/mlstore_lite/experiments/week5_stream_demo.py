import os
import shutil

from mlstore_lite.replication.cluster import Cluster
from mlstore_lite.replication.node import Node
from mlstore_lite.sharding import ShardGroup, ShardedCluster
from mlstore_lite.stream import (
    Consumer,
    EventLog,
    OffsetStore,
    Producer,
    StreamFeatureProcessor,
    TumblingWindow,
)


BASE_DIR = "demo_data/week5"


def reset_demo_dir() -> None:
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)


def make_node(shard_id: str, node_id: str, role: str) -> Node:
    return Node(
        node_id=node_id,
        db_dir=os.path.join(BASE_DIR, "store", shard_id, node_id),
        role=role,
        memtable_max_entries=20,
        compact_after=4,
    )


def make_shard_group(shard_id: str) -> ShardGroup:
    leader = make_node(shard_id, f"{shard_id}-leader", "leader")
    follower1 = make_node(shard_id, f"{shard_id}-follower1", "follower")
    follower2 = make_node(shard_id, f"{shard_id}-follower2", "follower")
    cluster = Cluster([leader, follower1, follower2], replication_mode="sync")
    return ShardGroup(shard_id=shard_id, cluster=cluster)


def make_store() -> ShardedCluster:
    return ShardedCluster(
        [
            make_shard_group("shard-a"),
            make_shard_group("shard-b"),
        ],
        virtual_nodes_per_shard=8,
    )


def main() -> None:
    reset_demo_dir()

    store = make_store()
    event_log = EventLog(os.path.join(BASE_DIR, "stream", "events.log"))
    offsets = OffsetStore(os.path.join(BASE_DIR, "stream", "offsets.json"))
    producer = Producer(event_log)
    consumer = Consumer(event_log, offsets, group_id="feature-updater")
    processor = StreamFeatureProcessor(
        consumer=consumer,
        store=store,
        window=TumblingWindow(size_seconds=60),
    )

    events = [
        {"user_id": "42", "event_type": "click", "timestamp": 10},
        {"user_id": "42", "event_type": "click", "timestamp": 20},
        {"user_id": "7", "event_type": "click", "timestamp": 35},
        {"user_id": "42", "event_type": "purchase", "amount": 19.99, "timestamp": 75},
        {"user_id": "7", "event_type": "purchase", "amount": 5.0, "timestamp": 80},
    ]

    print("\n=== WEEK 5 STREAM FEATURE DEMO ===")
    print("\nProducing events:")
    for event in events:
        offset = producer.send(event)
        print(f"offset {offset}: {event}")

    print("\nProcessing first two events:")
    print(processor.process_available(max_records=2))
    print("consumer offset:", consumer.current_offset())

    print("\nProcessing remaining events:")
    print(processor.process_available(max_records=10))
    print("consumer offset:", consumer.current_offset())

    print("\nStored stream features:")
    for shard_group in store.shard_groups.values():
        for key in sorted(shard_group.leader_snapshot().keys()):
            shard_id = store.get_shard_id(key)
            print(f"{key} = {store.get(key)}  (stored on {shard_id})")

    print("\nShard replica status:")
    for shard_status in store.cluster_status():
        print(shard_status)


if __name__ == "__main__":
    main()
