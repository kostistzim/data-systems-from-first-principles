import json
import os
from typing import Iterable, Optional


class EventLog:
    """
    Append-only JSON-lines event log.

    Offsets are integer positions in the log. A consumer stores the next offset
    it should read, which is the same convention used by many real log systems.
    """

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(self.path, "a", encoding="utf-8").close()
        self.next_offset = self._load_next_offset()

    def append(self, event: dict) -> int:
        offset = self.next_offset
        record = {"offset": offset, "event": event}

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, separators=(",", ":")))
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

        self.next_offset += 1
        return offset

    def read_from(
        self,
        offset: int,
        max_records: Optional[int] = None,
    ) -> list[dict]:
        if offset < 0:
            raise ValueError("offset must be >= 0")

        out: list[dict] = []
        for record in self.iter_records():
            if record["offset"] < offset:
                continue
            out.append(record)
            if max_records is not None and len(out) >= max_records:
                break
        return out

    def iter_records(self) -> Iterable[dict]:
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)

    def _load_next_offset(self) -> int:
        next_offset = 0
        for record in self.iter_records():
            next_offset = max(next_offset, int(record["offset"]) + 1)
        return next_offset
