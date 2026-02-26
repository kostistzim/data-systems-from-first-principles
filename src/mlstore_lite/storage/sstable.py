"""
sstable.py

SSTable = Sorted String Table (immutable, on-disk, sorted by key).

In our minimal version:
- The SSTable file is JSON Lines: one JSON object per line.
- Lines are sorted by key (ascending).
- Each record is either:
    {"k": "<key>", "t": 0, "v": "<value>"}   # normal value
    {"k": "<key>", "t": 1}                  # tombstone (deleted)

Why JSON lines?
- Easy to debug
- Handles tabs/newlines safely in keys/values without manual escaping

Read path:
- Because keys are sorted, we can scan and STOP early when current_key > target_key.
- For now this is still O(n) in worst case; later you can add an index/binary search.

Important:
- We provide lookup(key) that can return TOMBSTONE (not just None),
  so KVStore can distinguish:
    * "not present in this table"  -> None  (keep searching older tables)
    * "deleted in this table"      -> TOMBSTONE (STOP searching older tables)
"""

import json
import os
from typing import Iterator, Optional

from .memtable import Entry, TOMBSTONE, StoredValue


class SSTable:
    def __init__(self, path: str):
        self.path = path

    # -----------------------------
    # Writing
    # -----------------------------

    def write_from_entries(self, entries: Iterator[Entry]) -> None:
        """
        Write entries to this SSTable's path.

        Assumes entries are already sorted by key.
        """

        dir_path = os.path.dirname(self.path)
        os.makedirs(dir_path, exist_ok=True)

        tmp_path = self.path + ".tmp"

        with open(tmp_path, "w", encoding="utf-8") as f:
            for e in entries:
                if e.is_tombstone():
                    record = {"k": e.key, "t": 1}
                else:
                    record = {"k": e.key, "t": 0, "v": e.value}

                f.write(json.dumps(record))
                f.write("\n")

            f.flush() #flush() pushes Python’s buffered writes to the OS.
            os.fsync(f.fileno()) #fsync() asks the OS to force data to the physical disk.

        os.replace(tmp_path, self.path)

    # -----------------------------
    # Reading
    # -----------------------------

    def lookup(self, key: str) -> Optional[StoredValue]:
        """
        Returns:
          - string value
          - TOMBSTONE
          - None (not present)
        """

        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                record = json.loads(line)
                k = record["k"]

                # Early stop because file is sorted
                if k > key:
                    return None

                if k == key:
                    if record.get("t", 0) == 1:
                        return TOMBSTONE
                    return record["v"]

        return None

    def get(self, key: str) -> Optional[str]:
        """
        Returns only real values.
        Treats tombstone as deleted.
        """

        result = self.lookup(key)

        if result is None:
            return None

        if result is TOMBSTONE:
            return None

        return result

    def iter_entries(self) -> Iterator[Entry]:
        """
        Iterate through all entries in sorted order.
        """

        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                record = json.loads(line)

                if record.get("t", 0) == 1:
                    yield Entry(record["k"], TOMBSTONE)
                else:
                    yield Entry(record["k"], record["v"])