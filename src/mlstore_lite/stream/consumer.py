from typing import Optional

from .event_log import EventLog
from .offset_store import OffsetStore


class Consumer:
    def __init__(
        self,
        event_log: EventLog,
        offset_store: OffsetStore,
        group_id: str,
    ):
        self.event_log = event_log
        self.offset_store = offset_store
        self.group_id = group_id

    def poll(self, max_records: Optional[int] = None) -> list[dict]:
        offset = self.offset_store.get(self.group_id)
        return self.event_log.read_from(offset, max_records=max_records)

    def commit(self, records: list[dict]) -> None:
        if not records:
            return

        next_offset = max(record["offset"] for record in records) + 1
        self.offset_store.commit(self.group_id, next_offset)

    def current_offset(self) -> int:
        return self.offset_store.get(self.group_id)
