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


def test_event_log_appends_and_reads_from_offsets(tmp_path):
    event_log = EventLog(str(tmp_path / "events.log"))

    first_offset = event_log.append({"user_id": "42", "event_type": "click"})
    second_offset = event_log.append({"user_id": "7", "event_type": "purchase"})

    assert first_offset == 0
    assert second_offset == 1

    records = event_log.read_from(1)
    assert len(records) == 1
    assert records[0]["offset"] == 1
    assert records[0]["event"]["user_id"] == "7"


def test_consumer_tracks_group_offset(tmp_path):
    event_log = EventLog(str(tmp_path / "events.log"))
    offsets = OffsetStore(str(tmp_path / "offsets.json"))
    producer = Producer(event_log)
    consumer = Consumer(event_log, offsets, group_id="feature-updater")

    producer.send({"user_id": "42", "event_type": "click"})
    producer.send({"user_id": "7", "event_type": "click"})

    first_batch = consumer.poll(max_records=1)
    consumer.commit(first_batch)

    assert consumer.current_offset() == 1
    assert consumer.poll()[0]["offset"] == 1


def test_tumbling_window_assigns_fixed_windows():
    window = TumblingWindow(size_seconds=60)

    assert window.start_for(0) == 0
    assert window.start_for(59) == 0
    assert window.start_for(60) == 60
    assert window.end_for(60) == 120


def test_stream_processor_writes_windowed_features_to_store(tmp_path):
    store = make_store(tmp_path)
    event_log = EventLog(str(tmp_path / "stream" / "events.log"))
    offsets = OffsetStore(str(tmp_path / "stream" / "offsets.json"))
    producer = Producer(event_log)
    consumer = Consumer(event_log, offsets, group_id="feature-updater")
    processor = StreamFeatureProcessor(
        consumer=consumer,
        store=store,
        window=TumblingWindow(size_seconds=60),
    )

    producer.send({"user_id": "42", "event_type": "click", "timestamp": 10})
    producer.send({"user_id": "42", "event_type": "click", "timestamp": 20})
    producer.send(
        {"user_id": "42", "event_type": "purchase", "amount": 12.5, "timestamp": 70}
    )

    first_outputs = processor.process_available(max_records=2)
    second_outputs = processor.process_available(max_records=10)

    assert first_outputs["feature:user:42:window:0:event_count"] == 2
    assert first_outputs["feature:user:42:window:0:click_count"] == 2
    assert second_outputs["feature:user:42:window:60:event_count"] == 1
    assert second_outputs["feature:user:42:window:60:purchase_count"] == 1
    assert second_outputs["feature:user:42:window:60:total_purchase_amount"] == 12.5

    assert store.get("feature:user:42:window:0:click_count") == "2"
    assert store.get("feature:user:42:window:60:total_purchase_amount") == "12.5"
    assert consumer.current_offset() == 3

    for shard_group in store.shard_groups.values():
        for key, value in shard_group.leader_snapshot().items():
            for node in shard_group.cluster.nodes.values():
                assert node.get(key) == value


def test_stream_processor_accumulates_repeated_batches_in_same_window(tmp_path):
    store = make_store(tmp_path)
    event_log = EventLog(str(tmp_path / "stream" / "events.log"))
    offsets = OffsetStore(str(tmp_path / "stream" / "offsets.json"))
    producer = Producer(event_log)
    consumer = Consumer(event_log, offsets, group_id="feature-updater")
    processor = StreamFeatureProcessor(consumer, store, TumblingWindow(60))

    producer.send({"user_id": "42", "event_type": "click", "timestamp": 5})
    processor.process_available(max_records=1)

    producer.send({"user_id": "42", "event_type": "click", "timestamp": 30})
    processor.process_available(max_records=1)

    assert store.get("feature:user:42:window:0:click_count") == "2"
    assert consumer.current_offset() == 2
