""""
memtable.py
A MemTable is the in-memory component of an LSM style storage engine (DDIA Ch3 idea).
It holds the "latest" value for each key before we flush it to an on-disk SSTable.

-Fast writes: update an in-memory map (dict)
-Deletes are recorded as TOMBSTONES (not removed) so they still "win"
-When full, KVStore will flush MemTable to an SSTable in sorted-key order.
"""


#from __future__ import annotations , optional makes type hints as strings to prevent crushing.

from typing import Dict, Iterator, Optional, Union


# A unique marker object to represent "this key was deleted".
# We use an object() instead of None to avoid ambiguity.
# (If later you want to allow None as a real value, you're still safe.)
TOMBSTONE = object()

Value = str
StoredValue = Union[Value, object]  # either a real value (str) or TOMBSTONE

class Entry:
    def __init__(self, key: str, value: StoredValue):
        self.key = key
        self.value = value

    def is_tombstone(self) -> bool:
        return self.value is TOMBSTONE


class MemTable:
    def __init__(self, max_entries: int = 1000):
        self._data: Dict[str, StoredValue] = {}  # the underscore is a convention to indicate "private" members that should not be accessed from outside the class.
        self._max_entries = max_entries
    
    def put( self, key:str, value:str) -> None:
        self._data[key] = value

    def delete(self, key: str) -> None:
        self._data[key]= TOMBSTONE
    
    def get(self,key:str) -> Optional[str]:
        v = self._data.get(key)
        if v is None or v is TOMBSTONE:
            return None
        return v
    
    def should_flush(self) -> bool:
        return len(self._data) >= self._max_entries
    
    def iter_sorted_entries(self) -> Iterator[Entry]:
        for key in sorted(self._data.keys()):
            yield Entry(key, self._data[key]) #if we had 1 million keys, wed have to allocate memory for all of them at once.
            # By yielding one at a time, we can process them in a streaming fashion without needing to hold them all in memory at once.
    
    def clear(self) -> None:
        self._data.clear()
        
    def __len__(self) -> int:
        return len(self._data)

    def snapshot_dict(self) -> Dict[str, Optional[str]]:
        out: Dict[str, Optional[str]] = {}
        for k, v in self._data.items():
            out[k] = None if v is TOMBSTONE else v
        return out
