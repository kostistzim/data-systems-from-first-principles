from mlstore_lite.batch import BatchEngine, make_user_feature_job
from mlstore_lite.replication.cluster import Cluster
from mlstore_lite.replication.node import Node
from mlstore_lite.sharding import ShardGroup, ShardedCluster


def make_node(tmp_path, path_parts, node_id: str, role: str = "follower") -> Node:
    return Node(
        node_id=node_id,
        db_dir=str(tmp_path.joinpath(*path_parts, node_id)),
        role=role,
        memtable_max_entries=50,
        compact_after=10,
    )


def make_shard_group(tmp_path, shard_id: str) -> ShardGroup:
    leader = make_node(tmp_path, [shard_id], f"{shard_id}-leader", role="leader")
    follower1 = make_node(tmp_path, [shard_id], f"{shard_id}-follower1")
    follower2 = make_node(tmp_path, [shard_id], f"{shard_id}-follower2")
    cluster = Cluster([leader, follower1, follower2], replication_mode="sync")
    return ShardGroup(shard_id=shard_id, cluster=cluster)


def make_store(tmp_path) -> ShardedCluster:
    return ShardedCluster(
        [
            make_shard_group(tmp_path, "shard-a"),
            make_shard_group(tmp_path, "shard-b"),
        ],
        virtual_nodes_per_shard=8,
    )


def test_batch_engine_runs_map_shuffle_reduce():
    engine = BatchEngine(
        mapper=lambda value: [("even" if value % 2 == 0 else "odd", value)],
        reducer=lambda key, values: sum(values),
    )

    result = engine.run([1, 2, 3, 4])

    assert result.grouped_values == {"odd": [1, 3], "even": [2, 4]}
    assert result.outputs == {"odd": 4, "even": 6}


def test_batch_engine_retries_failed_map_task():
    attempts = {"count": 0}

    def flaky_mapper(value: int):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise ValueError("temporary map failure")
        return [("sum", value)]

    engine = BatchEngine(
        mapper=flaky_mapper,
        reducer=lambda key, values: sum(values),
        max_retries=1,
    )

    result = engine.run([5])

    assert attempts["count"] == 2
    assert result.outputs == {"sum": 5}


def test_user_feature_job_computes_expected_features():
    job = make_user_feature_job()
    events = [
        {"user_id": "42", "event_type": "click"},
        {"user_id": "42", "event_type": "click"},
        {"user_id": "42", "event_type": "purchase", "amount": 19.99},
        {"user_id": "7", "event_type": "purchase", "amount": 5.0},
    ]

    result = job.run(events)

    assert result.outputs["feature:user:42:event_count"] == 3
    assert result.outputs["feature:user:42:click_count"] == 2
    assert result.outputs["feature:user:42:purchase_count"] == 1
    assert result.outputs["feature:user:42:total_purchase_amount"] == 19.99
    assert result.outputs["feature:user:7:event_count"] == 1
    assert result.outputs["feature:user:7:purchase_count"] == 1
    assert result.outputs["feature:user:7:total_purchase_amount"] == 5


def test_user_feature_job_writes_features_to_sharded_store(tmp_path):
    store = make_store(tmp_path)
    job = make_user_feature_job()
    events = [
        {"user_id": "42", "event_type": "click"},
        {"user_id": "42", "event_type": "purchase", "amount": 10.0},
        {"user_id": "7", "event_type": "click"},
    ]

    outputs = job.write_to_store(events, store)

    assert outputs["feature:user:42:event_count"] == 2
    assert store.get("feature:user:42:event_count") == "2"
    assert store.get("feature:user:42:click_count") == "1"
    assert store.get("feature:user:42:purchase_count") == "1"
    assert store.get("feature:user:42:total_purchase_amount") == "10"
    assert store.get("feature:user:7:event_count") == "1"

    for shard_group in store.shard_groups.values():
        for key, value in shard_group.leader_snapshot().items():
            for node in shard_group.cluster.nodes.values():
                assert node.get(key) == value
