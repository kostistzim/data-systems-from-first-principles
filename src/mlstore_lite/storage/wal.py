import json
import os
from typing import Iterator, Tuple, Optional

class WAL:
    def __init__(self, path: str):
        self.path = path
        # Ensure the file exists so replay() can always open it.
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(self.path, "a", encoding="utf-8").close()

    def _append_record(self, record: dict) -> None:
        line = json.dumps(record, separators=(",", ":")) + "\n"
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())

    def append_put(self, key: str, value: str) -> None:
        self._append_record({"op": "put", "key": key, "value": value})

    def append_del(self, key: str) -> None:
        self._append_record({"op": "del", "key": key})

    def replay(self) -> Iterator[Tuple[str, str, Optional[str]]]:
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line) #this turns the dict into a json 
                op = rec["op"]
                if op == "put": 
                    yield ("put", rec["key"], rec["value"])
                elif op == "del":
                    yield ("del", rec["key"], None)
                else:
                    raise ValueError(f"Unknown WAL op: {op}")


#when we write append we mean add data to end of the file without modifying existing data. 