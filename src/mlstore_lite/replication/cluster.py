import threading
import time
from typing import Dict, List, Optional, Literal

from mlstore_lite.replication.node import Node


ReplicationMode = Literal["async", "sync"]


class Cluster:
    """
    Minimal leader-based replication coordinator.

    Responsibilities:
      - tracks leader and followers
      - assigns write indexes
      - routes client writes to the leader
      - replicates writes to followers
      - supports async/sync replication
      - supports manual failover
    """

    def __init__(
        self,
        nodes: List[Node],
        replication_mode: ReplicationMode = "async",
        follower_apply_delay_sec: float = 0.0,
    ):
        if not nodes:
            raise ValueError("Cluster requires at least one node")

        self.nodes: Dict[str, Node] = {node.node_id: node for node in nodes}
        self.replication_mode: ReplicationMode = replication_mode
        self.follower_apply_delay_sec = follower_apply_delay_sec

        leaders = [node for node in nodes if node.role == "leader"]
        if len(leaders) != 1:
            raise ValueError("Cluster must have exactly one leader")

        self.leader_id = leaders[0].node_id
        self.next_index = self._compute_start_index()

        self._bg_threads: List[threading.Thread] = []
        self._bg_lock = threading.Lock()

    # ----------------------------
    # Client API
    # ----------------------------

    def put(self, key: str, value: str) -> int:
        leader = self.get_leader()
        index = self.next_index
        self.next_index += 1

        # leader writes locally first
        leader.apply_client_put(index, key, value)

        # then replicate
        if self.replication_mode == "sync":
            self._replicate_put_sync(index, key, value)
        elif self.replication_mode == "async":
            self._replicate_put_async(index, key, value)
        else:
            raise ValueError(f"Unknown replication mode: {self.replication_mode}")

        return index

    def delete(self, key: str) -> int:
        leader = self.get_leader()
        index = self.next_index
        self.next_index += 1

        # leader deletes locally first
        leader.apply_client_delete(index, key)

        # then replicate
        if self.replication_mode == "sync":
            self._replicate_delete_sync(index, key)
        elif self.replication_mode == "async":
            self._replicate_delete_async(index, key)
        else:
            raise ValueError(f"Unknown replication mode: {self.replication_mode}")

        return index

    def get_from_leader(self, key: str) -> Optional[str]:
        return self.get_leader().get(key)

    def get_from_node(self, node_id: str, key: str) -> Optional[str]:
        return self.nodes[node_id].get(key)

    def wait_for_all_replication(self) -> None:
        """
        Wait for all background async replication tasks to finish.
        Useful in demos/tests.
        """
        while True:
            with self._bg_lock:
                alive_threads = [t for t in self._bg_threads if t.is_alive()]
                self._bg_threads = alive_threads
                if not self._bg_threads:
                    return

            for t in alive_threads:
                t.join(timeout=0.01)

    # ----------------------------
    # Replication internals
    # ----------------------------

    def _replicate_put_sync(self, index: int, key: str, value: str) -> None:
        for follower in self.get_followers():
            self._replicate_to_one_follower(follower, index, "put", key, value)

    def _replicate_delete_sync(self, index: int, key: str) -> None:
        for follower in self.get_followers():
            self._replicate_to_one_follower(follower, index, "delete", key, None)

    def _replicate_put_async(self, index: int, key: str, value: str) -> None:
        for follower in self.get_followers():
            self._start_async_replication(follower, index, "put", key, value)

    def _replicate_delete_async(self, index: int, key: str) -> None:
        for follower in self.get_followers():
            self._start_async_replication(follower, index, "delete", key, None)

    def _start_async_replication(
        self,
        follower: Node,
        index: int,
        op: str,
        key: str,
        value: Optional[str],
    ) -> None:
        thread = threading.Thread(
            target=self._replicate_to_one_follower,
            args=(follower, index, op, key, value),
            daemon=True,
        )
        thread.start()

        with self._bg_lock:
            self._bg_threads.append(thread)

    def _replicate_to_one_follower(
        self,
        follower: Node,
        index: int,
        op: str,
        key: str,
        value: Optional[str],
    ) -> None:
        self._maybe_delay_follower_apply()
        follower.apply_replication(index, op, key, value)

    def _maybe_delay_follower_apply(self) -> None:
        if self.follower_apply_delay_sec > 0:
            time.sleep(self.follower_apply_delay_sec)

    # ----------------------------
    # Cluster metadata
    # ----------------------------

    def get_leader(self) -> Node:
        return self.nodes[self.leader_id]

    def get_followers(self) -> List[Node]:
        return [
            node
            for node_id, node in self.nodes.items()
            if node_id != self.leader_id
        ]

    def set_replication_mode(self, mode: ReplicationMode) -> None:
        if mode not in ("async", "sync"):
            raise ValueError(f"Invalid replication mode: {mode}")
        self.replication_mode = mode

    def cluster_status(self) -> List[dict]:
        return [node.status() for node in self.nodes.values()]

    # ----------------------------
    # Manual failover
    # ----------------------------

    def promote_node_to_leader(self, node_id: str) -> None:
        """
        Manual failover:
        demote old leader, promote the chosen node.
        """
        if node_id not in self.nodes:
            raise ValueError(f"Unknown node_id: {node_id}")

        old_leader = self.get_leader()
        new_leader = self.nodes[node_id]

        if old_leader.node_id == new_leader.node_id:
            return

        old_leader.demote_to_follower()
        new_leader.promote_to_leader()
        self.leader_id = new_leader.node_id

        # ensure future indexes keep increasing
        self.next_index = self._compute_start_index()

    def most_up_to_date_follower(self) -> Node:
        followers = self.get_followers()
        if not followers:
            raise ValueError("No followers available")

        return max(followers, key=lambda node: node.last_applied_index)

    # ----------------------------
    # Helpers
    # ----------------------------

    def _compute_start_index(self) -> int:
        max_applied = max(node.last_applied_index for node in self.nodes.values())
        return max_applied + 1