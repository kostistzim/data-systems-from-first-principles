# src/mlstore_lite/replication/node.py

from typing import Optional, Literal

from mlstore_lite.storage.kvstore import KVStore


Role = Literal["leader", "follower"]


# some helper functions 





class Node:
    """
    A replication aware wrapper around one local KVStore.

    responsibilities:
    - knows if it is a leader or a follower
    - serves local reads
    - leader accepts client writes
    - follower accepts replicated writes from the leader
    - tracks last applied replication index
    """

    def __init__(
            self,
            node_id: str,
            db_dir: str,
            role: Role="follower",
            memtable_max_entries: int = 1000,
            compact_after: int = 4,
    ):
        self.node_id = node_id
        self.role: Role = role
        self.kv = KVStore(
            db_dir=db_dir,
            memtable_max_entries=memtable_max_entries,
            compact_after=compact_after,
        )
        self.last_applied_index = 0

    # ------
    # Reads
    # ------

    def get(self, key: str) ->Optional[str]:
        return self.kv.get(key)
    
    # -----
    # Client writes (only the leader)
    # -----

    def apply_client_put(self, index: int, key: str, value: str) -> None:
        #apply a client originated write on the leader

        self._require_role("leader")
        self._apply_put_with_index(index, key, value)
    
    def apply_client_delete(self, index: int, key:str) -> None:
        self._require_role("leader")
        self._apply_delete_with_index(index, key)


    #---------
    # replication writes , usually a follower
    #---------

    def apply_replication(
            self,
            index: int, 
            op: str,
            key: str,
            value: Optional[str] = None,
    ) -> None:
        """
        apply a replicated operation from the leader

        rules:
        - duplicate/old index : ignore
        - next expected index: apply
        - gap/out-of-order index: raise error
        """

        if index <= self.last_applied_index:
            return
        
        expected = self.last_applied_index + 1
        if index != expected:
            raise ValueError(
                f"Node {self.node_id}: out-of-order replication. "
                f"Expected index {expected}, got {index}"
            )
        
        if op == "put":
            if value is None:
                raise ValueError("Replication op 'put' requires a value")
            self._apply_put_with_index(index, key, value)
        elif op == "delete":
            self._apply_delete_with_index(index, key)
        else:
            raise ValueError(f"Unknown replication op: {op}")
        
    # ----------------------------
    # Role changes
    # ----------------------------

    def promote_to_leader(self) -> None:
        self.role = "leader"

    def demote_to_follower(self) -> None:
        self.role = "follower"

    # ----------------------------
    # Status / metadata
    # ----------------------------

    def status(self) -> dict:
        return {
            "node_id": self.node_id,
            "role": self.role,
            "last_applied_index": self.last_applied_index,
        }

    # ----------------------------
    # Internal helpers
    # ----------------------------

    def _apply_put_with_index(self, index: int, key: str, value: str) -> None:
        self.kv.put(key, value)
        self.last_applied_index = index

    def _apply_delete_with_index(self, index: int, key: str) -> None:
        self.kv.delete(key)
        self.last_applied_index = index

    def _require_role(self, required: Role) -> None:
        if self.role != required:
            raise ValueError(
                f"Node {self.node_id} is {self.role}, but {required} was required"
            )

