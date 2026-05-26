import os
from typing import Iterable, Optional

from mlstore_lite.batch import FeatureBatchJob, make_user_feature_job
from mlstore_lite.replication.cluster import Cluster, ReplicationMode
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


class MLStoreLiteSystem:
    """
    One object that wires together the implemented MLStore-Lite layers.
    """

    def __init__(
        self,
        store: ShardedCluster,
        batch_job: FeatureBatchJob,
        event_log: EventLog,
        producer: Producer,
        consumer: Consumer,
        stream_processor: StreamFeatureProcessor,
    ):
        self.store = store
        self.batch_job = batch_job
        self.event_log = event_log
        self.producer = producer
        self.consumer = consumer
        self.stream_processor = stream_processor

    def run_batch_features(self, events: Iterable[dict]) -> dict:
        return self.batch_job.write_to_store(events, self.store)

    def produce_event(self, event: dict) -> int:
        return self.producer.send(event)

    def produce_events(self, events: Iterable[dict]) -> list[int]:
        offsets: list[int] = []
        for event in events:
            offsets.append(self.produce_event(event))
        return offsets

    def process_stream_events(self, max_records: int = 100) -> dict:
        return self.stream_processor.process_available(max_records=max_records)

    def get_feature(self, key: str) -> Optional[str]:
        return self.store.get(key)

    def failover_shard(self, shard_id: str, node_id: Optional[str] = None) -> str:
        shard_group = self.store.get_shard_group(shard_id)

        if node_id is None:
            node_id = shard_group.cluster.most_up_to_date_follower().node_id

        shard_group.cluster.promote_node_to_leader(node_id)
        return node_id

    def status(self) -> dict:
        return {
            "consumer_offset": self.consumer.current_offset(),
            "key_distribution": self.store.key_distribution(),
            "shards": self.store.cluster_status(),
        }


def create_mlstore_lite_system(
    base_dir: str,
    shard_ids: Optional[list[str]] = None,
    replication_mode: ReplicationMode = "sync",
    virtual_nodes_per_shard: int = 8,
    window_size_seconds: int = 60,
    consumer_group_id: str = "feature-updater",
) -> MLStoreLiteSystem:
    if shard_ids is None:
        shard_ids = ["shard-a", "shard-b"]

    shard_groups = [
        _make_shard_group(base_dir, shard_id, replication_mode)
        for shard_id in shard_ids
    ]
    store = ShardedCluster(
        shard_groups,
        virtual_nodes_per_shard=virtual_nodes_per_shard,
    )

    event_log = EventLog(os.path.join(base_dir, "stream", "events.log"))
    offset_store = OffsetStore(os.path.join(base_dir, "stream", "offsets.json"))
    producer = Producer(event_log)
    consumer = Consumer(event_log, offset_store, group_id=consumer_group_id)
    stream_processor = StreamFeatureProcessor(
        consumer=consumer,
        store=store,
        window=TumblingWindow(window_size_seconds),
    )

    return MLStoreLiteSystem(
        store=store,
        batch_job=make_user_feature_job(),
        event_log=event_log,
        producer=producer,
        consumer=consumer,
        stream_processor=stream_processor,
    )


def _make_shard_group(
    base_dir: str,
    shard_id: str,
    replication_mode: ReplicationMode,
) -> ShardGroup:
    leader = _make_node(base_dir, shard_id, f"{shard_id}-leader", "leader")
    follower1 = _make_node(base_dir, shard_id, f"{shard_id}-follower1", "follower")
    follower2 = _make_node(base_dir, shard_id, f"{shard_id}-follower2", "follower")
    cluster = Cluster(
        [leader, follower1, follower2],
        replication_mode=replication_mode,
    )
    return ShardGroup(shard_id=shard_id, cluster=cluster)


def _make_node(base_dir: str, shard_id: str, node_id: str, role: str) -> Node:
    return Node(
        node_id=node_id,
        db_dir=os.path.join(base_dir, "store", shard_id, node_id),
        role=role,
        memtable_max_entries=50,
        compact_after=4,
    )
