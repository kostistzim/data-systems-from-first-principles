from mlstore_lite.storage.kvstore import KVStore


def test_flush_and_compaction(tmp_path):
    db_path = tmp_path / "db"
    db_path.mkdir()

    # Force flush quickly and compact quickly
    store = KVStore(str(db_path), memtable_max_entries=2, compact_after=3)

    # This will generate multiple flushes -> multiple SSTables -> compaction
    store.put("a", "1")
    store.put("b", "2")  # flush 1
    store.put("c", "3")
    store.put("d", "4")  # flush 2
    store.put("a", "5")
    store.put("e", "6")  # flush 3 -> triggers compaction

    # Ensure reads still correct
    assert store.get("a") == "5"
    assert store.get("b") == "2"
    assert store.get("e") == "6"

    # Restart should also work
    store2 = KVStore(str(db_path), memtable_max_entries=2, compact_after=3)
    assert store2.get("a") == "5"
    assert store2.get("b") == "2"
    assert store2.get("e") == "6"