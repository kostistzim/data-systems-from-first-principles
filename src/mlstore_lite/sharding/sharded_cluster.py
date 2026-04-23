from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from mlstore_lite.replication.cluster import Cluster

from .hash_ring import HashRing


@dataclass
class ShardGroup:
    shard_id: str
    cluster: Cluster

    def put(self, key: str, value: str) -> int:
        return self.cluster.put(key, value)

    def get(self, key: str) -> str | None:
        return self.cluster.get_from_leader(key)

    def delete(self, key: str) -> int:
        return self.cluster.delete(key)

    def wait_for_all_replication(self) -> None:
        self.cluster.wait_for_all_replication()

    def leader_snapshot(self) -> Dict[str, str]:
        return self.cluster.get_leader().snapshot_dict()

    def status(self) -> dict:
        return {
            "shard_id": self.shard_id,
            "leader_id": self.cluster.get_leader().node_id,
            "replicas": self.cluster.cluster_status(),
        }


class ShardedCluster:
    """
    Client-facing partitioning layer.

    It routes each key to a shard using consistent hashing. Each shard is a
    replicated Cluster, so partitioning is added on top of replication rather
    than replacing it.
    """

    def __init__(
        self,
        shard_groups: Iterable[ShardGroup],
        virtual_nodes_per_shard: int = 16,
    ):
        self.shard_groups: Dict[str, ShardGroup] = {}
        for shard_group in shard_groups:
            if shard_group.shard_id in self.shard_groups:
                raise ValueError(f"Duplicate shard_id: {shard_group.shard_id}")
            self.shard_groups[shard_group.shard_id] = shard_group

        if not self.shard_groups:
            raise ValueError("ShardedCluster requires at least one shard group")

        self.hash_ring = HashRing(
            self.shard_groups.keys(),
            virtual_nodes_per_shard=virtual_nodes_per_shard,
        )
        self._request_counts: Dict[str, int] = {
            shard_id: 0 for shard_id in self.shard_groups
        }

    def put(self, key: str, value: str) -> Tuple[str, int]:
        shard_id = self.get_shard_id(key)
        self._record_request(shard_id)
        index = self.shard_groups[shard_id].put(key, value)
        return shard_id, index

    def get(self, key: str) -> str | None:
        shard_id = self.get_shard_id(key)
        self._record_request(shard_id)
        return self.shard_groups[shard_id].get(key)

    def delete(self, key: str) -> Tuple[str, int]:
        shard_id = self.get_shard_id(key)
        self._record_request(shard_id)
        index = self.shard_groups[shard_id].delete(key)
        return shard_id, index

    def get_shard_id(self, key: str) -> str:
        return self.hash_ring.get_shard(key)

    def get_shard_group(self, shard_id: str) -> ShardGroup:
        return self.shard_groups[shard_id]

    def wait_for_all_replication(self) -> None:
        for shard_group in self.shard_groups.values():
            shard_group.wait_for_all_replication()

    def add_shard_group(self, shard_group: ShardGroup) -> None:
        if shard_group.shard_id in self.shard_groups:
            raise ValueError(f"Duplicate shard_id: {shard_group.shard_id}")

        self.shard_groups[shard_group.shard_id] = shard_group
        self.hash_ring.add_shard(shard_group.shard_id)
        self._request_counts[shard_group.shard_id] = 0

    def rebalance_keys(self) -> List[dict]:
        """
        Move live keys to the shard that now owns them under the current ring.

        This is intentionally simple: it scans each shard leader's visible data
        and moves keys one by one. It is enough for experiments and for showing
        how adding a shard changes ownership.
        """
        movements: List[dict] = []

        for source_shard_id, shard_group in self.shard_groups.items():
            for key, value in shard_group.leader_snapshot().items():
                target_shard_id = self.get_shard_id(key)
                if target_shard_id == source_shard_id:
                    continue

                self.shard_groups[target_shard_id].put(key, value)
                shard_group.delete(key)
                movements.append(
                    {
                        "key": key,
                        "from_shard": source_shard_id,
                        "to_shard": target_shard_id,
                    }
                )

        self.wait_for_all_replication()
        return movements

    def key_distribution(self) -> Dict[str, int]:
        return {
            shard_id: len(shard_group.leader_snapshot())
            for shard_id, shard_group in self.shard_groups.items()
        }

    def request_counts(self) -> Dict[str, int]:
        return dict(self._request_counts)

    def hotspot_report(self) -> List[dict]:
        return sorted(
            [
                {"shard_id": shard_id, "requests": count}
                for shard_id, count in self._request_counts.items()
            ],
            key=lambda item: item["requests"],
            reverse=True,
        )

    def cluster_status(self) -> List[dict]:
        return [
            self.shard_groups[shard_id].status()
            for shard_id in sorted(self.shard_groups.keys())
        ]

    def _record_request(self, shard_id: str) -> None:
        self._request_counts[shard_id] += 1
