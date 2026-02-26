# src/mlstore_lite/storage/kvstore.py

import os
from typing import List, Optional

from .wal import WAL
from .memtable import MemTable, TOMBSTONE
from .sstable import SSTable
from .compaction import Compactor


class KVStore:
    def __init__(
        self,
        db_dir: str,
        memtable_max_entries: int = 1000,
        compact_after: int = 4,  # when SSTable count reaches this, compact
    ):
        self.db_dir = db_dir
        os.makedirs(self.db_dir, exist_ok=True)

        # WAL
        self.wal_path = os.path.join(self.db_dir, "wal.log")
        self.wal = WAL(self.wal_path)

        # MemTable
        self.mem = MemTable(max_entries=memtable_max_entries)

        # SSTables (newest first)
        self.sstables: List[SSTable] = self._load_sstables()

        self.compact_after = compact_after
        self.compactor = Compactor(self.db_dir)

        # Recovery: replay WAL into MemTable
        for op, key, value in self.wal.replay():
            if op == "put":
                self.mem.put(key, value)
            elif op == "del":
                self.mem.delete(key)

        # If replay overfills, flush (keeps startup deterministic)
        if self.mem.should_flush():
            self._flush_memtable()

    # ----------------------------
    # Public API
    # ----------------------------

    def put(self, key: str, value: str) -> None:
        self.wal.append_put(key, value)
        self.mem.put(key, value)

        if self.mem.should_flush():
            self._flush_memtable()

    def delete(self, key: str) -> None:
        self.wal.append_del(key)
        self.mem.delete(key)

        if self.mem.should_flush():
            self._flush_memtable()

    def get(self, key: str) -> Optional[str]:
        # 1) MemTable first (must distinguish tombstone vs missing)
        v = self.mem._data.get(key, None)  # ok for now; later add a mem.lookup()
        if v is not None:
            if v is TOMBSTONE:
                return None
            return v  # str

        # 2) SSTables newest -> oldest
        for table in self.sstables:
            found = table.lookup(key)
            if found is None:
                continue
            if found is TOMBSTONE:
                return None
            return found  # str

        return None

    # ----------------------------
    # Internals: SSTables
    # ----------------------------

    def _load_sstables(self) -> List[SSTable]:
        files = []
        for name in os.listdir(self.db_dir):
            if name.startswith("sst_") and name.endswith(".dat"):
                files.append(name)

        def table_num(fname: str) -> int:
            stem = fname[len("sst_") : -len(".dat")]
            try:
                return int(stem)
            except ValueError:
                return -1

        files.sort(key=table_num, reverse=True)  # newest first
        return [
            SSTable(os.path.join(self.db_dir, f))
            for f in files
            if table_num(f) >= 0
        ]

    def _next_sstable_path(self) -> str:
        max_n = 0
        for t in self.sstables:
            base = os.path.basename(t.path)
            stem = base[len("sst_") : -len(".dat")]
            try:
                max_n = max(max_n, int(stem))
            except ValueError:
                pass

        next_n = max_n + 1
        return os.path.join(self.db_dir, f"sst_{next_n:06d}.dat")

    def _reset_wal(self) -> None:
        """
        Simple WAL truncation:
        After data is safely in SSTables and MemTable is cleared, we can reset wal.log.
        """
        # close + recreate is safest, but we don't know your WAL internals.
        # This brute force truncation is enough for this project stage:
        with open(self.wal_path, "w", encoding="utf-8") as f:
            f.flush()
            os.fsync(f.fileno())

        # Recreate WAL object so future appends go to the truncated file cleanly
        self.wal = WAL(self.wal_path)

    def _flush_memtable(self) -> None:
        if len(self.mem) == 0:
            return

        path = self._next_sstable_path()
        table = SSTable(path)
        table.write_from_entries(self.mem.iter_sorted_entries())

        # New table is newest
        self.sstables.insert(0, table)

        # Clear memtable after successful write
        self.mem.clear()

        # Reset WAL so replay doesn't grow forever
        self._reset_wal()

        # Maybe compact
        if len(self.sstables) >= self.compact_after:
            self._compact_all()

    def _compact_all(self) -> None:
        """
        Compacts all SSTables into one.
        """
        # Output file should get a new number (higher than existing).
        out_path = self._next_sstable_path()

        new_table = self.compactor.compact(self.sstables, out_path)

        # Delete old tables, keep the new one
        old = self.sstables
        self.sstables = [new_table]
        self.compactor.delete_tables(old)

        # Reset WAL again (safe and keeps it small)
        self._reset_wal()