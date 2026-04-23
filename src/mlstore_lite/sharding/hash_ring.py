import bisect
import hashlib
from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class RingEntry:
    token: int
    shard_id: str
    virtual_node: int


class HashRing:
    """
    Minimal consistent hash ring.

    Each shard appears multiple times on the ring through virtual nodes so
    distribution is smoother than a single point per shard.
    """

    def __init__(
        self,
        shard_ids: Iterable[str] = (),
        virtual_nodes_per_shard: int = 16,
    ):
        if virtual_nodes_per_shard <= 0:
            raise ValueError("virtual_nodes_per_shard must be > 0")

        self.virtual_nodes_per_shard = virtual_nodes_per_shard
        self._entries: List[RingEntry] = []
        self._tokens: List[int] = []

        for shard_id in shard_ids:
            self.add_shard(shard_id)

    def add_shard(self, shard_id: str) -> None:
        if shard_id in self.shard_ids():
            raise ValueError(f"Shard {shard_id} already exists in the ring")

        for virtual_node in range(self.virtual_nodes_per_shard):
            token = self._hash_text(f"{shard_id}::{virtual_node}")
            self._entries.append(
                RingEntry(token=token, shard_id=shard_id, virtual_node=virtual_node)
            )

        self._rebuild_ring()

    def remove_shard(self, shard_id: str) -> None:
        if shard_id not in self.shard_ids():
            raise ValueError(f"Unknown shard_id: {shard_id}")

        self._entries = [entry for entry in self._entries if entry.shard_id != shard_id]
        self._rebuild_ring()

    def get_shard(self, key: str) -> str:
        if not self._entries:
            raise ValueError("Hash ring has no shards")

        token = self._hash_text(key)
        index = bisect.bisect_left(self._tokens, token)
        if index == len(self._tokens):
            index = 0
        return self._entries[index].shard_id

    def shard_ids(self) -> List[str]:
        return sorted({entry.shard_id for entry in self._entries})

    def describe(self) -> List[dict]:
        return [
            {
                "token": entry.token,
                "shard_id": entry.shard_id,
                "virtual_node": entry.virtual_node,
            }
            for entry in self._entries
        ]

    def _rebuild_ring(self) -> None:
        self._entries.sort(key=lambda entry: (entry.token, entry.shard_id))
        self._tokens = [entry.token for entry in self._entries]

    @staticmethod
    def _hash_text(text: str) -> int:
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()
        return int(digest, 16)
