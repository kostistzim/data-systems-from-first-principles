from mlstore_lite.storage.kvstore import KVStore
import os
import shutil

def test_put_and_recover(tmp_path):
    db_path = tmp_path / "db"
    db_path.mkdir()

    # First instance
    store1 = KVStore(str(db_path))
    store1.put("a", "1")

    # Simulate restart (new instance)
    store2 = KVStore(str(db_path))

    assert store2.get("a") == "1"
