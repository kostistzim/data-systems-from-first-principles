# src/mlstore_lite/kvstore.py
import os # filesystem helpers, create directories,join paths etc.
from .wal import WAL #imports our WAL class from wal.py

class KVStore:
    def __init__(self, db_dir: str):  #db_dir is the directory where this db stores files (wal for now, later sstables)
        self.db_dir = db_dir
        os.makedirs(self.db_dir, exist_ok=True) #make sure db dir exists, if it already exists do nothing (exist_ok=True)

        wal_path = os.path.join(self.db_dir, "wal.log") #the path to the wal file is db_dir/wal.log
        self.wal = WAL(wal_path) # this creates a WAL object that append and replay operations.

        self.mem: dict[str, str] = {} #This is our “current database contents” for now.

        for op, key, value in self.wal.replay(): # read WAL records from disk in order and iterate over them. Each record
            # represents something/an event that happend previously. 
            if op == "put":
                self.mem[key] = value #If WAL says “put key=value”, apply it to memory. after replay, self.mem should match the latest state.
            elif op == "del": # if WAL says “delete key”, remove it from memory. 
                self.mem.pop(key, None) 

    def put(self, key: str, value: str) -> None:
        self.wal.append_put(key, value)
        self.mem[key] = value

    def get(self, key: str):
        return self.mem.get(key, None)

    def delete(self, key: str):
        self.wal.append_del(key)
        self.mem.pop(key, None)
