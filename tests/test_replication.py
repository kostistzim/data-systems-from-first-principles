import time

from mlstore_lite.replication.cluster import Cluster
from mlstore_lite.replication.node import Node


class SlowFirstReplicationNode(Node):
    def apply_replication(self, index: int, op: str, key: str, value=None) -> None:
        if index == 1:
            time.sleep(0.05)
        super().apply_replication(index, op, key, value)


def make_node(tmp_path, node_id: str, role: str = "follower", node_cls=Node) -> Node:
    return node_cls(
        node_id=node_id,
        db_dir=str(tmp_path / node_id),
        role=role,
        memtable_max_entries=50,
        compact_after=10,
    )


def test_sync_replication_put_and_delete(tmp_path):
    leader = make_node(tmp_path, "leader", role="leader")
    follower1 = make_node(tmp_path, "follower1")
    follower2 = make_node(tmp_path, "follower2")

    cluster = Cluster([leader, follower1, follower2], replication_mode="sync")

    first_index = cluster.put("feature:user42", "0.91")
    second_index = cluster.delete("feature:user42")

    assert first_index == 1
    assert second_index == 2

    for node_id in ("leader", "follower1", "follower2"):
        assert cluster.get_from_node(node_id, "feature:user42") is None
        assert cluster.nodes[node_id].last_applied_index == 2


def test_async_replication_shows_stale_read_until_followers_catch_up(tmp_path):
    leader = make_node(tmp_path, "leader", role="leader")
    follower = make_node(tmp_path, "follower")

    cluster = Cluster(
        [leader, follower],
        replication_mode="async",
        follower_apply_delay_sec=0.05,
    )

    cluster.put("feature:user7", "42")

    assert cluster.get_from_leader("feature:user7") == "42"
    assert cluster.get_from_node("follower", "feature:user7") is None

    cluster.wait_for_all_replication()

    assert cluster.get_from_node("follower", "feature:user7") == "42"
    assert cluster.nodes["follower"].last_applied_index == 1


def test_async_replication_preserves_per_follower_write_order(tmp_path):
    leader = make_node(tmp_path, "leader", role="leader")
    slow_follower = make_node(
        tmp_path, "follower", node_cls=SlowFirstReplicationNode
    )

    cluster = Cluster([leader, slow_follower], replication_mode="async")

    cluster.put("model_version", "v1")
    cluster.put("model_version", "v2")
    cluster.wait_for_all_replication()

    assert cluster.get_from_node("follower", "model_version") == "v2"
    assert cluster.nodes["follower"].last_applied_index == 2


def test_manual_failover_promotes_new_leader_and_continues_replication(tmp_path):
    leader = make_node(tmp_path, "leader", role="leader")
    follower1 = make_node(tmp_path, "follower1")
    follower2 = make_node(tmp_path, "follower2")

    cluster = Cluster([leader, follower1, follower2], replication_mode="sync")

    cluster.put("model_version", "v1")
    cluster.promote_node_to_leader("follower1")
    next_index = cluster.put("model_version", "v2")

    assert next_index == 2
    assert cluster.get_leader().node_id == "follower1"

    for node_id in ("leader", "follower1", "follower2"):
        assert cluster.get_from_node(node_id, "model_version") == "v2"
        assert cluster.nodes[node_id].last_applied_index == 2


def test_cluster_rejects_duplicate_node_ids(tmp_path):
    leader = make_node(tmp_path, "node-a", role="leader")
    duplicate = make_node(tmp_path, "node-a")

    try:
        Cluster([leader, duplicate], replication_mode="sync")
    except ValueError as exc:
        assert "unique node ids" in str(exc)
    else:
        raise AssertionError("Cluster should reject duplicate node ids")
