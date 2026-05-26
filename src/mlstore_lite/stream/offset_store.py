import json
import os


class OffsetStore:
    """
    Small file-backed store for consumer group offsets.

    The stored value is the next offset a consumer should read.
    """

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(self.path):
            self._write_offsets({})

    def get(self, group_id: str) -> int:
        offsets = self._read_offsets()
        return int(offsets.get(group_id, 0))

    def commit(self, group_id: str, next_offset: int) -> None:
        if next_offset < 0:
            raise ValueError("next_offset must be >= 0")

        offsets = self._read_offsets()
        offsets[group_id] = next_offset
        self._write_offsets(offsets)

    def _read_offsets(self) -> dict:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_offsets(self, offsets: dict) -> None:
        tmp_path = self.path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(offsets, f, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, self.path)
