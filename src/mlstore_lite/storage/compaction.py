# src/mlstore_lite/storage/compaction.py

import os
from typing import List, Dict

from .memtable import Entry, TOMBSTONE
from .sstable import SSTable


class Compactor:
    """
    Minimal compactor: merges multiple SSTables into a single SSTable.

    Correctness rule:
      - Newest SSTable wins for each key.
      - Tombstone means "deleted" and should override older values.
    """

    def __init__(self, db_dir: str):
        self.db_dir = db_dir

    def compact(self, sstables_newest_first: List[SSTable], out_path: str) -> SSTable:
        """
        Compacts ALL provided SSTables into one new SSTable at out_path.

        Implementation strategy (simple, not memory-optimal):
          - Build a dict of final key -> value/tombstone by applying SSTables
            from OLDEST to NEWEST, so newest overwrites.
          - Write sorted entries to out SSTable.
        """
        if not sstables_newest_first:
            raise ValueError("No SSTables to compact")

        # Apply oldest -> newest so newest overwrites
        final: Dict[str, object] = {}

        for table in reversed(sstables_newest_first):
            for e in table.iter_entries():
                final[e.key] = e.value

        # Write to a brand new SSTable file
        # We need sorted entries for SSTable writing.
        def sorted_entries():
            for k in sorted(final.keys()):
                yield Entry(k, final[k])

        out = SSTable(out_path)
        out.write_from_entries(sorted_entries())
        return out

    def delete_tables(self, tables: List[SSTable]) -> None:
        """Remove old SSTable files from disk (best-effort)."""
        for t in tables:
            try:
                os.remove(t.path)
            except FileNotFoundError:
                pass