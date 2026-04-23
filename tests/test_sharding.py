from mlstore_lite.replication.cluster import Cluster
from mlstore_lite.replication.node import Node
from mlstore_lite.sharding import HashRing, ShardGroup, ShardedCluster


def make_node(tmp_path, path_parts, node_id: str, role: str = "follower") -> Node:
    return Node(
        node_id=node_id,
        db_dir=str(tmp_path.joinpath(*path_parts, node_id)),
        role=role,
        memtable_max_entries=50,
        compact_after=10,
    )


def make_shard_group(tmp_path, shard_id: str, replication_mode: str = "sync") -> ShardGroup:
    leader = make_node(tmp_path, [shard_id], f"{shard_id}-leader", role="leader")
    follower1 = make_node(tmp_path, [shard_id], f"{shard_id}-follower1")
    follower2 = make_node(tmp_path, [shard_id], f"{shard_id}-follower2")
    cluster = Cluster(
        [leader, follower1, follower2],
        replication_mode=replication_mode,
    )
    return ShardGroup(shard_id=shard_id, cluster=cluster)


def test_hash_ring_creates_virtual_nodes_and_stable_routing():
    ring = HashRing(["shard-a", "shard-b"], virtual_nodes_per_shard=8)

    assert len(ring.describe()) == 16
    assert ring.get_shard("user:42") == ring.get_shard("user:42")


def test_sharded_cluster_routes_writes_to_one_replicated_shard(tmp_path):
    shard_a = make_shard_group(tmp_path, "shard-a")
    shard_b = make_shard_group(tmp_path, "shard-b")
    cluster = ShardedCluster([shard_a, shard_b], virtual_nodes_per_shard=8)

    shard_id, index = cluster.put("feature:user42", "0.91")
    cluster.wait_for_all_replication()

    assert index == 1
    assert cluster.get("feature:user42") == "0.91"

    target_group = cluster.get_shard_group(shard_id)
    other_shard_id = "shard-b" if shard_id == "shard-a" else "shard-a"
    other_group = cluster.get_shard_group(other_shard_id)

    for node in target_group.cluster.nodes.values():
        assert node.get("feature:user42") == "0.91"

    for node in other_group.cluster.nodes.values():
        assert node.get("feature:user42") is None


def test_rebalancing_moves_keys_after_adding_a_shard(tmp_path):
    shard_a = make_shard_group(tmp_path, "shard-a")
    cluster = ShardedCluster([shard_a], virtual_nodes_per_shard=16)

    expected = {f"user:{i}": str(i) for i in range(40)}
    for key, value in expected.items():
        cluster.put(key, value)

    new_shard = make_shard_group(tmp_path, "shard-b")
    cluster.add_shard_group(new_shard)
    movements = cluster.rebalance_keys()

    assert movements

    for key, value in expected.items():
        assert cluster.get(key) == value

    distribution = cluster.key_distribution()
    assert distribution["shard-a"] > 0
    assert distribution["shard-b"] > 0
    assert sum(distribution.values()) == len(expected)

    for shard_id, shard_group in cluster.shard_groups.items():
        for key in shard_group.leader_snapshot():
            assert cluster.get_shard_id(key) == shard_id


def test_request_counts_track_router_load(tmp_path):
    shard_a = make_shard_group(tmp_path, "shard-a")
    shard_b = make_shard_group(tmp_path, "shard-b")
    cluster = ShardedCluster([shard_a, shard_b], virtual_nodes_per_shard=8)

    cluster.put("user:1", "A")
    cluster.get("user:1")
    cluster.delete("user:1")

    counts = cluster.request_counts()
    assert sum(counts.values()) == 3
    assert cluster.hotspot_report()[0]["requests"] >= cluster.hotspot_report()[-1]["requests"]
