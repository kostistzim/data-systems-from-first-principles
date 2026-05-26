import os
import shutil

from mlstore_lite.batch import make_user_feature_job
from mlstore_lite.replication.cluster import Cluster
from mlstore_lite.replication.node import Node
from mlstore_lite.sharding import ShardGroup, ShardedCluster


BASE_DIR = "demo_data/week4"


def reset_demo_dir() -> None:
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)


def make_node(shard_id: str, node_id: str, role: str) -> Node:
    return Node(
        node_id=node_id,
        db_dir=os.path.join(BASE_DIR, shard_id, node_id),
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
    job = make_user_feature_job()

    events = [
        {"user_id": "42", "event_type": "click"},
        {"user_id": "42", "event_type": "click"},
        {"user_id": "42", "event_type": "purchase", "amount": 19.99},
        {"user_id": "7", "event_type": "click"},
        {"user_id": "7", "event_type": "purchase", "amount": 5.0},
        {"user_id": "9", "event_type": "click"},
    ]

    print("\n=== WEEK 4 BATCH FEATURE DEMO ===")
    print("\nInput events:")
    for event in events:
        print(event)

    outputs = job.write_to_store(events, store)

    print("\nComputed feature outputs:")
    for key in sorted(outputs):
        shard_id = store.get_shard_id(key)
        print(f"{key} = {store.get(key)}  (stored on {shard_id})")

    print("\nShard key distribution:")
    print(store.key_distribution())

    print("\nShard replica status:")
    for shard_status in store.cluster_status():
        print(shard_status)


if __name__ == "__main__":
    main()
