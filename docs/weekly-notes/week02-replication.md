# MLStore-Lite: Week 2 Notes
## Leader-Based Replication

## 1. Why Replication Comes After Storage

Week 1 solved the question:

```text
How does one machine store data correctly?
```

Week 2 moves to the next systems question:

```text
How do several machines keep copies of the same data?
```

That is what **replication** means.

Replication matters because a single machine is fragile:

- it can crash
- it can be unavailable
- it can become a bottleneck

If several nodes keep copies of the same data, the system becomes more resilient.

In MLStore-Lite, replication is built on top of the storage engine from Week 1. Each replica is still a local storage engine. Replication is the coordination layer above it.

---

## 2. What Replication Means In This Project

In this project, replication means:

- one node is the **leader**
- other nodes are **followers**
- clients send writes to the leader
- the leader applies the write locally
- the leader then sends the same write to followers
- followers apply that write in the same order

So the system does not have one shared disk or one shared memory state.

Instead, it has multiple independent nodes, and each node stores its own local copy using the Week 1 storage engine.

If replication works correctly, those copies should converge to the same result.

---

## 3. Important Terms

### 3.1 Replica

A **replica** is one copy of the data on one node.

If three nodes all store the same key-value state, then the system has three replicas.

### 3.2 Leader

The **leader** is the node that accepts client writes.

It is the source of truth for write ordering.

In this project, the leader:

- receives `put` and `delete`
- assigns an operation index
- writes to its local storage engine
- forwards the operation to followers

### 3.3 Follower

A **follower** is a replica that does not accept normal client writes directly.

Instead, it receives replicated operations from the leader and applies them locally.

### 3.4 Replication Lag

**Replication lag** means a follower is behind the leader.

Example:

- leader has already applied write 10
- follower has only applied up to write 8

Then the follower is lagging by two writes.

### 3.5 Failover

**Failover** means switching leadership from one node to another when needed.

In this project, failover is manual, not automatic.

That keeps the scope realistic while still letting the project demonstrate the idea.

---

## 4. The Architecture

The Week 2 replication layer adds two main abstractions.

### 4.1 Node

A `Node` is a replication-aware wrapper around one local `KVStore`.

This is important:

- the `KVStore` is still the storage engine
- the `Node` adds replication behavior around it

So a node knows:

- its role: leader or follower
- how to serve local reads
- how to apply client writes if it is the leader
- how to apply replicated writes if it is a follower
- the last operation index it has applied

### 4.2 Cluster

A `Cluster` coordinates several nodes.

Its responsibilities are:

- keep track of which node is leader
- route writes to the leader
- assign increasing operation indexes
- replicate writes to followers
- support sync and async replication
- support manual failover

You can think of the cluster as the control layer above individual nodes.

So the system now looks like:

```text
Client
  ↓
Cluster
  ↓
Node
  ↓
KVStore
  ↓
WAL + MemTable + SSTables + Compaction
```

This layering is important for the whole project.

---

## 5. How Storage Connects to Replication

This is the key connection between Week 1 and Week 2.

Each node in the cluster contains its own storage engine.

That means when the leader replicates an operation, the follower does not just keep it in memory. The follower writes it into its own `KVStore`, which then uses:

- its own WAL
- its own MemTable
- its own SSTables
- its own compaction logic

So replication is not replacing storage. It is reusing storage on several machines.

Another way to say it:

- storage gives each node a reliable local state
- replication makes several local states evolve in the same direction

This is one of the most important ideas in the project.

---

## 6. Ordered Operations and Why They Matter

Replication is not only about sending the same writes to many followers.

It is also about sending them in the same order.

Example:

```text
1. put("model_version", "v1")
2. put("model_version", "v2")
```

If a follower applied step 2 before step 1, it could end in the wrong final state.

That is why the cluster assigns a strictly increasing **operation index**:

- write 1 gets index 1
- write 2 gets index 2
- write 3 gets index 3

Each node tracks `last_applied_index`.

This gives a simple rule:

- old or duplicate index: ignore
- next expected index: apply
- out-of-order index: reject

This is a simplified but very useful replication discipline.

---

## 7. Write Flow

When a client writes to the system, the flow is:

1. client sends write to the cluster
2. cluster forwards it to the current leader
3. cluster assigns the next operation index
4. leader applies the write locally
5. leader replicates the same write to followers
6. followers apply it to their own local storage engines

This gives one logical write, but several physical copies.

Example:

```text
put("feature:user42:ctr_7d", "0.13")
```

After replication, that key should exist on:

- the leader's storage engine
- follower 1's storage engine
- follower 2's storage engine

---

## 8. Sync vs Async Replication

This project implements two modes.

### 8.1 Synchronous replication

In **sync replication**, the leader waits for followers to apply the write before the client call returns.

Meaning:

- slower writes
- stronger confidence that followers already have the data

If the write returns successfully, the replicas are expected to be caught up.

### 8.2 Asynchronous replication

In **async replication**, the leader returns to the client first and followers catch up later.

Meaning:

- faster writes
- followers may be temporarily stale

This is where **replication lag** becomes visible.

A follower read right after the leader acknowledges a write may still return an older value or no value yet.

This is not automatically a bug. It is the tradeoff of asynchronous replication.

---

## 9. Stale Reads

A **stale read** happens when a follower is behind and serves older data than the leader.

Example:

```text
Leader has:   feature_A -> 42
Follower has: feature_A -> not yet applied
```

If the client reads from the follower too early, it may get:

```text
None
```

even though the leader already has the value.

This is a central concept for the final report because it shows a real tradeoff:

- low latency writes with async replication
- but weaker read freshness on followers

---

## 10. Manual Failover

If the leader is no longer the one we want to use, the cluster can manually promote another node.

In MLStore-Lite:

1. old leader is demoted
2. chosen follower is promoted
3. future writes go to the new leader

This is intentionally simpler than a real consensus-based system.

There is no automated leader election here.

That is acceptable for this course because the goal is to understand leader-based replication clearly without adding the much larger topic of consensus algorithms.

---

## 11. What Was Implemented In Code

At this stage, the replication layer supports:

- leader and follower roles
- local reads from any node
- client writes through the leader
- ordered replication with operation indexes
- synchronous replication
- asynchronous replication
- manual failover
- replication status through `last_applied_index`

The replication layer also now preserves per-follower write order during async replication, which is important for correctness.

That means if two writes happen quickly, a follower still applies them in index order.

---

## 12. Why Operation Order Needed Extra Care

There is a subtle systems point here.

In async mode, replication uses background threads.

That is convenient because it models followers catching up later. However, background concurrency can create a correctness problem:

- write 2 could reach a follower before write 1 finishes
- then the follower would see an out-of-order sequence

The fix is to preserve order **per follower**.

That means:

- different followers can still progress in parallel
- but each individual follower applies operations one by one in index order

This is a good example of a distributed systems lesson:

being concurrent is not enough; you must also preserve correctness constraints.

---

## 13. What This Layer Does Not Try To Solve

This Week 2 design does not include:

- consensus algorithms
- automatic leader election
- quorum protocols
- network partitions
- cross-node transactions
- geographically distributed deployment

Those topics are important in real systems, but they are beyond the intended scope of this project.

Here, the goal is a small but understandable leader-based replication model.

---

## 14. Why This Matters For The Rest Of The Project

Replication is a bridge between local storage and later distributed scaling.

It teaches the project how to answer:

- where writes should go
- how copies stay in sync
- what consistency tradeoffs exist

This becomes especially important before partitioning.

Later, when the project adds sharding, the natural design is:

- one shard
- one leader for that shard
- several followers for that shard

So the Week 2 replication cluster becomes the building block that future partitions can reuse.

---

## 15. Short Summary

Week 2 extends the Week 1 storage engine into a replicated system.

The storage engine is still the local persistence layer on each node.

Replication adds:

- a leader
- followers
- ordered writes
- sync and async modes
- failover

The main systems intuition is:

- storage makes one node reliable
- replication makes several nodes hold the same logical data

That gives MLStore-Lite its first true distributed systems layer and prepares it for partitioning in the next phase.
