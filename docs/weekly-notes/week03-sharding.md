# MLStore-Lite: Week 3 Notes
## Partitioning and Data Distribution

## 1. Why Partitioning Comes After Replication

By the end of Week 2, MLStore-Lite could already keep multiple copies of the same data through leader-based replication.

That solved the question:

```text
How do several nodes hold the same data?
```

Week 3 solves a different question:

```text
How do we split a large dataset across several replica groups?
```

That is what **partitioning** or **sharding** means.

So the distinction is:

- replication = multiple copies of the same shard
- partitioning = different shards own different keys

Both are needed:

- replication gives resilience
- partitioning gives scale

---

## 2. The Main Idea

After partitioning, the system no longer has one replication cluster for all keys.

Instead, it has several shard groups.

Each shard group is:

- one shard
- one leader
- two followers

So in the current project examples, the intended replication factor is:

```text
RF = 3 = 1 leader + 2 followers per shard
```

So the system changes from:

```text
Client -> one Cluster -> Nodes
```

to:

```text
Client -> Router / ShardedCluster -> one shard's Cluster -> Nodes
```

The client still writes a key like:

```text
put("user:42", "0.91")
```

but now the system must first answer:

```text
Which shard owns "user:42"?
```

Only then can it forward the request to the correct replication cluster.

---

## 3. Important Terms

### 3.1 Partition / Shard

A **partition** or **shard** is one subset of the total keyspace.

If the whole dataset is split into three shards, then each shard owns only some keys, not all keys.

### 3.2 Router

The **router** is the layer that receives a key and decides where it should go.

In MLStore-Lite, this role is handled by `ShardedCluster`.

### 3.3 Hashing

**Hashing** means turning a key into a numeric value.

Example:

```text
"user:42" -> 128734...
```

That numeric value is then used to choose a shard.

### 3.4 Consistent Hashing

**Consistent hashing** places shards on a logical ring of hash values.

A key is assigned to the first shard clockwise from the key's hash value.

The important advantage is:

- when a new shard is added, only some keys move
- most keys stay where they already were

This is better than simpler schemes like `hash(key) % N`, where changing `N` can remap almost everything.

### 3.5 Virtual Nodes

A **virtual node** means a physical shard appears several times on the ring.

Why this helps:

- smoother distribution
- less chance that one shard gets a very uneven portion of the ring

So instead of one point per shard, we use many ring positions per shard.

---

## 4. Architecture After Week 3

The system now has three conceptual layers:

```text
Client
  ↓
ShardedCluster / Router
  ↓
ShardGroup
  ↓
Cluster
  ↓
Node
  ↓
KVStore
  ↓
WAL + MemTable + SSTables + Compaction
```

This layering is the key architecture of the project so far.

What each layer means:

- `KVStore`: local storage engine
- `Node`: one replica using that storage engine
- `Cluster`: replication group for one shard
- `ShardGroup`: small wrapper representing one shard
- `ShardedCluster`: router across shards

This is the first point where the project becomes a true distributed data layout rather than only replicated copies.

---

## 5. What Was Implemented

The partitioning layer includes:

- a `HashRing`
- virtual nodes per shard
- a `ShardGroup` wrapper
- a `ShardedCluster` router
- request routing for `put`, `get`, and `delete`
- simple rebalancing when a shard is added
- request counters for hotspot-style visibility

The design intentionally reuses the Week 2 replication code instead of modifying it deeply.

That is an important architectural choice.

---

## 6. Why This Design Reuses Replication

Partitioning does not replace replication.

Instead, each shard is itself a replicated group.

So when the router maps a key to `shard-b`, the request is not sent to a single machine. It is sent to the replication cluster responsible for `shard-b`.

That means:

- partitioning decides **where** a key belongs
- replication decides **how copies of that shard stay synchronized**

This is exactly the connection that often feels confusing at first. They solve different problems, but they fit together cleanly.

---

## 7. Routing Flow

For a write like:

```text
put("feature:user42:ctr_7d", "0.13")
```

the flow is:

1. the router hashes the key
2. the hash ring chooses a shard
3. the router forwards the write to that shard group
4. the shard leader applies the write locally
5. the shard leader replicates it to followers

So one key only belongs to one shard, but that shard may have several replicas.

This gives both:

- horizontal partitioning
- fault-tolerant copies

In the current project setup, that means each key is stored on exactly one shard group, and inside that shard group it is copied to three replicas.

---

## 8. Rebalancing

Rebalancing means adjusting data placement after the ring changes.

In this project, the main case is:

- add a new shard
- update the hash ring
- move the keys that now belong to the new shard

The implementation here is intentionally simple:

- scan live keys from shard leaders
- check where each key now belongs under the new ring
- if ownership changed, write it to the new shard and delete it from the old shard

This is enough to demonstrate the main systems idea:

adding capacity should not require moving all data, only the data whose ownership changed.

---

## 9. Hotspots

A **hotspot** happens when one shard gets disproportionate load.

That can happen because:

- some keys are much more popular than others
- data distribution is imperfect
- the workload is skewed

The current implementation tracks request counts per shard.

This is a simple way to see whether one shard is handling more routed traffic than the others.

It is not a full production load-balancing system, but it is enough for experiments and for the final report discussion.

---

## 10. Why Consistent Hashing Helps

Consistent hashing is useful because the cluster membership may change over time.

If a new shard is added, we want:

- some keys to move
- but not all keys

That is the main benefit of a ring-based approach.

The project also uses virtual nodes so that shard ownership is spread more evenly.

Without virtual nodes, one shard could easily end up owning a much larger section of the ring than another.

---

## 11. What This Layer Does Not Try To Solve

This Week 3 design does not include:

- automatic background migration protocols
- transactional movement of keys between shards
- leader changes during rebalancing
- range-based partitioning
- complex hotspot mitigation

Those are all real topics in large systems, but the current implementation is meant to stay understandable and aligned with the course scope.

---

## 12. Short Summary

Week 3 turns MLStore-Lite from one replicated key-value cluster into a sharded distributed store.

The core ideas are:

- hash each key
- route it to a shard
- let that shard's replication cluster store the data
- rebalance only the keys whose ownership changes when a new shard is added

The most important intuition is:

- storage = how one node stores data
- replication = how one shard keeps copies
- partitioning = how the full keyspace is split across shards

That gives the system its first scalable distributed architecture and prepares it for later batch and stream processing work.
