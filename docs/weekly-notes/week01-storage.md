# MLStore-Lite: Storage Engine Design Notes (Phase 1 – Week 1)

## 1. Overview

This week focused on implementing a minimal write-optimized storage engine inspired by *Designing Data-Intensive Applications* (Chapter 3). The goal was not performance parity with industrial systems like RocksDB or Cassandra, but to deeply understand the architectural principles behind log-structured storage.

The system we built, **MLStore-Lite**, implements:

- Write-Ahead Logging (WAL)
- In-memory MemTable
- Immutable Sorted String Tables (SSTables)
- Basic compaction
- Crash recovery

This forms a minimal **Log-Structured Merge Tree (LSM-tree)** architecture.

---

## 2. Architectural Overview

At a high level, the system consists of four core components:

```
Client
  ↓
KVStore (orchestrator)
  ├── WAL (durable append-only log)
  ├── MemTable (in-memory state)
  └── SSTables (immutable sorted files)
```

The system follows a **write-optimized design**:

- Writes are sequential (fast)
- Reads may require checking multiple structures
- Periodic compaction reduces read amplification

---

## 3. Write Path

The write path is intentionally ordered for durability.

### PUT(key, value)

1. Append operation to WAL (fsync).
2. Apply update to MemTable.
3. If MemTable exceeds threshold → flush to SSTable.

### DELETE(key)

1. Append delete operation to WAL.
2. Insert a tombstone into MemTable.
3. Possibly trigger flush.

The strict ordering is:

```
WAL append → MemTable update
```

This guarantees durability. If a crash occurs after WAL write but before memory update, recovery will replay the log and reconstruct state.

If the order were reversed, data loss would be possible.

---

## 4. Write-Ahead Log (WAL)

The WAL is an append-only JSON-lines file:

```json
{"op":"put","key":"a","value":"1"}
{"op":"del","key":"b"}
```

Properties:

- Sequential disk writes (fast on HDD/SSD).
- Fsync ensures persistence.
- Replay on startup reconstructs MemTable state.

### Why append-only?

Sequential disk I/O is dramatically faster than random writes. The WAL leverages this property.

### Crash Recovery

On startup:

- WAL is replayed in order.
- Each operation is applied to a fresh MemTable.
- System state becomes deterministic.

---

## 5. MemTable

The MemTable is an in-memory dictionary storing the most recent state.

Key features:

- O(1) average lookup and insert.
- Stores both values and tombstones.
- Tracks size for flush threshold.

### Tombstones

Instead of deleting keys outright, we store a special `TOMBSTONE` object.

Why?

Because once data is flushed to disk, older SSTables may still contain previous values. If we simply removed keys from memory, older on-disk data could "resurrect" deleted keys.

Tombstones ensure deletion semantics survive flushing and compaction.

---

## 6. SSTables

SSTables are immutable, sorted, on-disk segment files.

Example format (JSON lines):

```json
{"k":"a","t":0,"v":"1"}
{"k":"b","t":1}
```

Where:
- `t = 0` → value
- `t = 1` → tombstone

Properties:

- Sorted by key.
- Written atomically (temp file → rename).
- Never modified after creation.

### Why sorted?

Sorted order enables:

- Early termination during lookup.
- Future binary search or sparse indexing.
- Efficient compaction (merge sorted streams).

---

## 7. Read Path

Lookup order is critical:

1. Check MemTable.
2. Check SSTables from newest to oldest.

Newest data must win.

Example:

```
SSTable_1: a → 1
SSTable_2: a → TOMBSTONE
```

Correct result for `get("a")` must be `None`.

If we searched oldest first, stale values would reappear.

---

## 8. Flushing

When MemTable reaches a threshold:

1. Its contents are written to a new SSTable.
2. MemTable is cleared.
3. WAL is truncated/reset.

Flushing converts in-memory state into immutable disk state.

Tradeoff:

- Smaller threshold → more SSTables → higher read amplification.
- Larger threshold → more memory usage, fewer flushes.

---

## 9. Compaction

Compaction merges multiple SSTables into one.

Algorithm (simplified):

1. Iterate SSTables from oldest to newest.
2. For each key, newest value overwrites older ones.
3. Write merged sorted output into new SSTable.
4. Delete old SSTables.

Effects:

- Reduces number of files.
- Reduces read amplification.
- Eliminates obsolete overwritten values.
- Preserves tombstones correctly.

Compaction trades CPU and disk I/O for improved read performance.

---

## 10. Tradeoffs

### Write Amplification

Data may be written multiple times:

- WAL
- Initial SSTable
- Compaction outputs

This increases total bytes written.

### Read Amplification

Reads may require checking:

- MemTable
- Multiple SSTables

Compaction mitigates this.

### Space Amplification

Old values and tombstones temporarily consume disk space until compaction removes them.

---

## 11. Why LSM Instead of B-Trees?

B-tree systems:

- Modify data in place.
- Random writes.
- Good read locality.

LSM systems:

- Append-only writes.
- Sequential disk usage.
- Excellent write throughput.

LSM is especially suited for:

- Write-heavy workloads.
- Log/event ingestion.
- ML feature stores.
- Time-series data.

---

## 12. System Properties Achieved

The current MLStore-Lite guarantees:

- Durability (via WAL + fsync).
- Crash recovery.
- Correct delete semantics.
- Immutable on-disk segments.
- Basic compaction.
- Deterministic startup state.

This forms a correct single-node storage engine.

---

## 13. Limitations

- No indexing inside SSTables (linear scan).
- No Bloom filters.
- No multi-level compaction.
- No concurrency control.
- No replication.
- No sharding.

These are deliberate omissions for clarity.

---

## 14. Transition to Replication

Replication builds naturally on this architecture.

Key insight:

The WAL already functions as an ordered stream of mutations.

Replication can be implemented by:

- Streaming WAL entries to follower nodes.
- Replaying them in order.
- Ensuring followers apply operations deterministically.

Thus, the storage layer becomes the foundation for:

- Leader-based replication.
- Log shipping.
- Eventually consistent experiments.

---

## 15. Conceptual Summary

This week implemented a minimal LSM-tree:

- Writes are sequential and durable.
- Reads check memory first, then immutable disk segments.
- Compaction merges sorted segments.
- Tombstones preserve delete correctness.
- Recovery is log-driven and deterministic.

This architecture mirrors the foundational ideas behind:

- LevelDB
- RocksDB
- Cassandra
- HBase

Understanding this structure is essential before layering replication and distributed concerns on top.

---

## Conclusion

The current MLStore-Lite implementation achieves a functioning write-optimized storage engine with crash recovery and compaction. It demonstrates core tradeoffs of LSM-based systems and provides a solid foundation for implementing leader-based replication in the next phase.