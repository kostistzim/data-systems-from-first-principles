# MLStore-Lite: Week 1 Notes
## Storage Engine Foundations

## 1. Why This Week Matters

Before a distributed system can replicate data or split data across machines, it first needs a correct way to store data on one machine.

That is the purpose of the **storage engine**.

In this project, the storage engine is the part of MLStore-Lite that answers questions like:

- How is a write stored safely?
- What happens if the process crashes?
- Where does data live before it is written to disk?
- How do reads find the newest value for a key?

This week implements a **single-node key-value store** inspired by the LSM-tree ideas in DDIA Chapter 3.

The result is a minimal but correct storage layer with:

- a write-ahead log (`WAL`)
- an in-memory table (`MemTable`)
- immutable disk files (`SSTables`)
- compaction
- crash recovery

This is the foundation that the replication layer builds on later.

---

## 2. What Is a Storage Engine?

A **storage engine** is the low-level part of a database that is responsible for:

- storing data
- reading data back
- keeping data durable across crashes
- deciding how data is laid out on disk

In MLStore-Lite, the storage engine is not the whole system. It is the local persistence layer used by one node.

You can think of the system in layers:

```text
Client API
    ↓
KVStore
    ↓
WAL + MemTable + SSTables + Compaction
```

So when a client does:

```text
put("user:42", "0.91")
```

the storage engine is the part that makes sure that write is preserved and later returned by:

```text
get("user:42")
```

---

## 3. Main Components

The Week 1 design has four main pieces.

### 3.1 WAL

The **write-ahead log** is an append-only file on disk.

Every write is first recorded in the WAL before the in-memory state is updated.

Example records:

```json
{"op":"put","key":"a","value":"1"}
{"op":"del","key":"b"}
```

Why it exists:

- If the process crashes, the WAL still contains the recent writes.
- On restart, the system can replay the WAL and rebuild state.

Important idea:

The WAL gives the system **durability**.

### 3.2 MemTable

The **MemTable** is an in-memory dictionary holding the latest values for keys.

Why it exists:

- Memory is fast.
- Recent writes can be served without going to disk.

The MemTable is temporary. When it becomes large enough, it is flushed to disk.

### 3.3 SSTables

An **SSTable** is an immutable, sorted file on disk.

SSTable means **Sorted String Table**.

Important properties:

- keys are stored in sorted order
- files are never modified after creation
- new disk state is created by writing a new file, not editing an old one

Why sorted files are useful:

- lookups can stop early
- merging files is easier
- compaction becomes more natural

### 3.4 Compaction

Over time, many SSTables accumulate.

**Compaction** merges them into a smaller number of newer SSTables.

Its job is to:

- remove overwritten values
- preserve only the newest version of a key
- keep delete markers correct
- reduce the number of files reads must check

---

## 4. The Core Idea: LSM-Tree Style Storage

This design follows the ideas of an **LSM-tree**.

LSM stands for **Log-Structured Merge Tree**.

The big idea is:

- writes are first cheap and sequential
- cleanup and merging happen later

That is different from a structure like a B-tree, where data is often updated in place.

Why this matters:

- sequential writes are usually efficient
- the design fits write-heavy systems
- many real systems use this idea, including RocksDB, Cassandra, and LevelDB

This is one reason LSM-style storage is a good conceptual fit for ML feature storage and event-heavy systems.

---

## 5. Write Path

The **write path** means: what happens when the user writes data?

For `put(key, value)`, the order is:

1. append the operation to the WAL
2. update the MemTable
3. if needed, flush the MemTable into a new SSTable

For `delete(key)`, the order is:

1. append a delete record to the WAL
2. store a tombstone in the MemTable
3. flush later if needed

The key ordering rule is:

```text
WAL first -> memory second
```

Why this order matters:

- If the process crashes after the WAL write, recovery can replay it.
- If memory were updated first and the WAL write never happened, that update could be lost.

So the WAL comes first because it is the durable record.

---

## 6. Read Path

The **read path** means: where does the system look when someone calls `get(key)`?

The lookup order is:

1. check the MemTable
2. if not found, check SSTables from newest to oldest

Why newest-to-oldest matters:

Because old disk files may contain stale values.

Example:

```text
Older SSTable:  user:42 -> "0.4"
Newer SSTable:  user:42 -> "0.9"
```

The correct answer is `"0.9"`.

So the system must search the newest state first.

---

## 7. Deletes and Tombstones

Deletes in LSM-style storage are not handled by physically removing old data everywhere immediately.

Instead, the system writes a **tombstone**.

A tombstone is a special marker meaning:

```text
this key has been deleted
```

Why that is necessary:

Suppose an old SSTable on disk still contains:

```text
user:42 -> "0.9"
```

If we simply removed `user:42` from memory and did nothing else, a later read might still find the old disk value and incorrectly think the key still exists.

The tombstone prevents that.

So tombstones are not an implementation detail only. They are part of the correctness of delete behavior.

---

## 8. Flushing

The MemTable cannot grow forever.

When it reaches a threshold, the system **flushes** it:

1. sort the MemTable entries
2. write them into a new SSTable
3. clear the MemTable
4. reset the WAL

This moves recent in-memory state into durable immutable disk state.

Tradeoff:

- small MemTable: more frequent flushes, more SSTables
- large MemTable: fewer flushes, more memory usage

---

## 9. Compaction

Compaction is the cleanup step of the storage engine.

Without compaction, the system would keep accumulating SSTables, which would make reads more expensive.

In MLStore-Lite, compaction:

1. reads several SSTables
2. keeps only the newest value for each key
3. preserves tombstones correctly
4. writes one new merged SSTable
5. deletes the old files

Why compaction exists:

- it reduces read amplification
- it removes obsolete values
- it keeps the on-disk state manageable

Compaction costs CPU and disk I/O, so it is a tradeoff:

- better reads later
- extra work during cleanup

---

## 10. Crash Recovery

Crash recovery is one of the most important reasons the WAL exists.

On restart:

1. the system opens the WAL
2. replays each recorded operation
3. rebuilds the MemTable
4. continues serving reads and writes

This gives the system a deterministic recovery path.

That means the storage engine can recover recent writes that were durable in the log even if they were not yet flushed into SSTables.

---

## 11. What Has Been Built So Far

At the end of Week 1, MLStore-Lite supports:

- durable single-node writes
- reads that return the newest visible value
- correct delete behavior
- crash recovery
- immutable on-disk sorted segments
- basic compaction

This is enough to call it a working single-node storage engine.

It is not a full production database, but it correctly demonstrates the core ideas.

---

## 12. Tradeoffs of This Design

This design is intentionally simple, but the important tradeoffs are already visible.

### 12.1 Write amplification

The same logical data may be written multiple times:

- once to the WAL
- once to an SSTable
- again during compaction

### 12.2 Read amplification

A read may need to check:

- the MemTable
- several SSTables

### 12.3 Space amplification

Old values and tombstones may remain on disk until compaction removes them.

These tradeoffs are central to LSM-style systems.

---

## 13. What Is Missing

The Week 1 storage engine deliberately does not include:

- replication
- partitioning
- concurrency control
- indexes inside SSTables
- bloom filters
- advanced compaction strategies

These omissions are useful because they keep the storage layer understandable.

---

## 14. How Storage Connects to Replication

This is the natural bridge into Week 2.

A single node can now:

- store key-value data
- recover after crashes
- maintain an ordered history of recent writes through the WAL

Replication builds on top of that.

The key idea is:

- one node can accept writes locally
- other nodes can apply the same writes in the same order
- if they all use the same storage engine, they should converge to the same state

So storage answers:

```text
How does one machine store data correctly?
```

Replication answers:

```text
How do several machines keep copies of that data?
```

That is why storage comes first.

---

## 15. Short Summary

Week 1 built the local persistence layer of MLStore-Lite.

The storage engine uses:

- a WAL for durability
- a MemTable for fast recent writes
- SSTables for immutable disk storage
- compaction for cleanup

This gives the project a solid single-node base.

The next natural step is replication: taking this one-node design and making several nodes keep consistent copies of the same data.
