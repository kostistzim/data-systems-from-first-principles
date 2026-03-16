import os
import shutil
import time

from mlstore_lite.replication.node import Node
from mlstore_lite.replication.cluster import Cluster


BASE_DIR = "demo_data/week2"


def reset_demo_dir() -> None:
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)


def make_node(node_id: str, role: str) -> Node:
    return Node(
        node_id=node_id,
        db_dir=os.path.join(BASE_DIR, node_id),
        role=role,
        memtable_max_entries=3,   # small to trigger flushes during demo
        compact_after=4,
    )


def print_status(cluster: Cluster, title: str) -> None:
    print(f"\n=== {title} ===")
    for status in cluster.cluster_status():
        print(status)


def async_demo() -> None:
    print("\n" + "=" * 60)
    print("ASYNC REPLICATION DEMO")
    print("=" * 60)

    leader = make_node("node1", "leader")
    follower1 = make_node("node2", "follower")
    follower2 = make_node("node3", "follower")

    cluster = Cluster(
        [leader, follower1, follower2],
        replication_mode="async",
        follower_apply_delay_sec=2.0,
    )

    print_status(cluster, "Initial cluster state")

    print("\nWriting: feature_A = 42")
    idx = cluster.put("feature_A", "42")
    print(f"Write assigned index: {idx}")

    print("\nImmediate reads right after leader ack:")
    print("Leader read:", cluster.get_from_leader("feature_A"))
    print("Follower node2 read:", cluster.get_from_node("node2", "feature_A"))
    print("Follower node3 read:", cluster.get_from_node("node3", "feature_A"))

    print("\nSleeping 2.5 seconds so followers can catch up...")
    time.sleep(2.5)
    cluster.wait_for_all_replication()

    print("\nReads after replication delay:")
    print("Leader read:", cluster.get_from_leader("feature_A"))
    print("Follower node2 read:", cluster.get_from_node("node2", "feature_A"))
    print("Follower node3 read:", cluster.get_from_node("node3", "feature_A"))

    print_status(cluster, "After async replication catches up")


def sync_demo() -> None:
    print("\n" + "=" * 60)
    print("SYNC REPLICATION DEMO")
    print("=" * 60)

    leader = make_node("node4", "leader")
    follower1 = make_node("node5", "follower")
    follower2 = make_node("node6", "follower")

    cluster = Cluster(
        [leader, follower1, follower2],
        replication_mode="sync",
        follower_apply_delay_sec=1.5,
    )

    print_status(cluster, "Initial cluster state")

    print("\nWriting: feature_B = 100")
    start = time.time()
    idx = cluster.put("feature_B", "100")
    elapsed = time.time() - start

    print(f"Write assigned index: {idx}")
    print(f"Client observed write latency: {elapsed:.3f} sec")

    print("\nImmediate reads after sync write returns:")
    print("Leader read:", cluster.get_from_leader("feature_B"))
    print("Follower node5 read:", cluster.get_from_node("node5", "feature_B"))
    print("Follower node6 read:", cluster.get_from_node("node6", "feature_B"))

    print_status(cluster, "After sync replication")


def failover_demo() -> None:
    print("\n" + "=" * 60)
    print("MANUAL FAILOVER DEMO")
    print("=" * 60)

    leader = make_node("node7", "leader")
    follower1 = make_node("node8", "follower")
    follower2 = make_node("node9", "follower")

    cluster = Cluster(
        [leader, follower1, follower2],
        replication_mode="sync",
        follower_apply_delay_sec=0.0,
    )

    print("\nWrite before failover: model_version = v1")
    cluster.put("model_version", "v1")

    print_status(cluster, "Before failover")

    best_follower = cluster.most_up_to_date_follower()
    print(f"\nPromoting follower {best_follower.node_id} to leader")
    cluster.promote_node_to_leader(best_follower.node_id)

    print_status(cluster, "After failover")

    print("\nWrite after failover: model_version = v2")
    cluster.put("model_version", "v2")

    print("\nReads after failover:")
    print("Current leader read:", cluster.get_from_leader("model_version"))
    for node_id in ["node7", "node8", "node9"]:
        print(f"{node_id} read:", cluster.get_from_node(node_id, "model_version"))

    print_status(cluster, "Final cluster state")


def main() -> None:
    reset_demo_dir()
    async_demo()
    sync_demo()
    failover_demo()


if __name__ == "__main__":
    main()