# MLStore-Lite: Week 4 Notes
## Batch Processing and Feature Computation

## 1. Why Batch Processing Comes After Sharding

Weeks 1-3 built the storage side of MLStore-Lite:

- Week 1: one node can store data correctly
- Week 2: several nodes can replicate the same data
- Week 3: different keys can be routed to different shards

Week 4 adds a new kind of layer.

Instead of asking:

```text
How do we store data?
```

batch processing asks:

```text
How do we compute useful derived data from many input records?
```

This connects to DDIA Chapter 10.

The important idea is that many data systems are not only used for storing raw facts. They are also used to transform raw facts into derived views, aggregates, indexes, or features.

For an ML-style system, this means turning raw events into features.

---

## 2. What Batch Processing Means Here

In this project, batch processing means:

- take a finite collection of input records
- process all of them
- compute aggregate feature values
- write the results into MLStore-Lite

Example input records:

```text
user 42 clicked
user 42 clicked
user 42 purchased 19.99
```

Example computed features:

```text
feature:user:42:event_count = 3
feature:user:42:click_count = 2
feature:user:42:purchase_count = 1
feature:user:42:total_purchase_amount = 19.99
```

The raw events are the input.

The features are derived data.

---

## 3. Map, Shuffle, Reduce

The Week 4 batch engine follows a small MapReduce-style structure:

```text
map -> shuffle -> reduce
```

This is not a full MapReduce system like Hadoop. It is a local teaching implementation of the same core dataflow.

### 3.1 Map

The map step looks at one input record and emits zero or more intermediate key-value pairs.

Example:

```text
input event:
{"user_id": "42", "event_type": "click"}

mapped output:
("feature:user:42:event_count", 1)
("feature:user:42:click_count", 1)
```

The map step does not need to know about all events. It only interprets one record at a time.

### 3.2 Shuffle

The shuffle step groups intermediate values by key.

Example:

```text
("feature:user:42:click_count", 1)
("feature:user:42:click_count", 1)
```

becomes:

```text
"feature:user:42:click_count" -> [1, 1]
```

This grouping is the bridge between individual records and aggregate results.

### 3.3 Reduce

The reduce step takes one grouped key and its list of values, then computes the final output.

Example:

```text
"feature:user:42:click_count" -> [1, 1]
```

becomes:

```text
"feature:user:42:click_count" -> 2
```

So the reducer turns grouped intermediate values into the final feature value.

---

## 4. Architecture After Week 4

The system now has a batch layer above the sharded store:

```text
Raw events
  ↓
BatchEngine
  ↓
FeatureBatchJob
  ↓
ShardedCluster
  ↓
ShardGroup
  ↓
Cluster
  ↓
Node
  ↓
KVStore
```

The lower layers still mean the same thing:

- `KVStore`: local storage
- `Cluster`: replication
- `ShardedCluster`: partitioning and routing

The new layer means:

- `BatchEngine`: generic Map -> Shuffle -> Reduce execution
- `FeatureBatchJob`: MLStore-specific feature computation

This is a useful separation.

The batch engine does not need to know about users or purchases.

The feature job does not need to know how replication or SSTables work.

Each layer has a narrower responsibility.

---

## 5. What Was Implemented

The Week 4 implementation includes:

- a reusable local batch engine
- map/shuffle/reduce execution
- simple retry behavior for map and reduce tasks
- a user-feature batch job
- writing computed features into the sharded store
- a runnable Week 4 demo
- tests for the batch engine and feature output

The implemented feature job currently computes:

- per-user event count
- per-user click count
- per-user purchase count
- per-user total purchase amount

The output keys use the feature-style naming convention:

```text
feature:user:<user_id>:<feature_name>
```

---

## 6. Why This Connects To ML Infrastructure

Machine learning systems often do not train or serve directly from raw application logs.

They usually need features.

Raw event:

```text
user 42 clicked item 123
```

Feature:

```text
how many times did user 42 click recently?
```

The batch layer is where raw historical data becomes a feature table.

In this project, MLStore-Lite acts like a small feature store:

- batch job computes features
- features are written into the sharded key-value store
- later systems can read features by key

This gives the project a clearer AI/ML infrastructure angle.

---

## 7. Retry Behavior

The batch engine includes a small retry mechanism.

If a map or reduce task raises an exception, the engine can retry it a limited number of times.

This models a key batch-processing idea:

```text
tasks can fail, and the system can retry the failed unit of work
```

The implementation is local and simple.

It does not include distributed workers, task scheduling, or checkpointing.

But it gives the project a concrete way to discuss local fault recovery.

---

## 8. What This Layer Does Not Try To Solve

This Week 4 design does not include:

- distributed worker processes
- parallel execution
- external file formats such as Parquet
- a real scheduler
- cluster-wide fault tolerance
- incremental streaming updates

Those are larger systems topics.

Week 4 focuses on the conceptual dataflow: map records, group values, reduce groups, and write derived data.

---

## 9. Code Map

The main Week 4 implementation lives in:

- `src/mlstore_lite/batch/engine.py`
- `src/mlstore_lite/batch/features.py`
- `src/mlstore_lite/experiments/week4_demo.py`
- `tests/test_batch.py`

What each file does:

- `engine.py`: generic local Map -> Shuffle -> Reduce engine
- `features.py`: user-event feature computation and writes to MLStore-Lite
- `week4_demo.py`: runnable demo showing batch features written into the sharded store
- `test_batch.py`: verifies map/shuffle/reduce, retries, feature computation, and writes into the sharded store

---

## 10. How This Week Is Verified

The main Week 4 verification is:

- `tests/test_batch.py`

This verifies:

- the generic batch engine groups and reduces records correctly
- failed map tasks can be retried
- user features are computed correctly
- features are written into `ShardedCluster`
- replicated shard nodes receive the computed feature values

The runnable demo is:

```text
python -m mlstore_lite.experiments.week4_demo
```

That demo shows raw events, computed feature outputs, shard placement, and replica status.

---

## 11. Short Summary

Week 4 adds derived-data computation to MLStore-Lite.

The core idea is:

```text
raw events -> batch computation -> features -> sharded replicated store
```

This is the first layer that looks directly like ML infrastructure.

The previous weeks built the storage substrate.

Week 4 starts using that substrate to compute and store features.
