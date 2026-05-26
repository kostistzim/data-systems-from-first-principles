# MLStore-Lite Weekly Notes

This directory is the running implementation diary for the course project.

At the moment, the code implementation is complete through:

- Week 1: storage engine
- Week 2: replication
- Week 3: partitioning / sharding
- Week 4: batch processing
- Week 5-6: stream processing

The later files remain placeholders because those parts of the system have not been implemented yet:

- Week 7: integration
- Week 8: evaluation

## How To Read These Notes

The notes are meant to be read in order:

1. `week01-storage.md`
2. `week02-replication.md`
3. `week03-sharding.md`
4. `week04-batch.md`
5. `week05-stream.md`
6. `week06-stream.md`

That order follows the architecture of the system itself:

```text
single-node storage
    -> replicated node groups
    -> sharded distributed system
    -> batch feature computation
    -> stream feature updates
```

## Current Project Story

So far, MLStore-Lite can:

- store data durably on one node
- recover after crashes
- replicate writes across several replicas
- support sync and async replication
- fail over manually to a new leader
- partition keys across shards
- rebalance keys when a shard is added
- compute batch features from raw events
- write batch features into the sharded replicated store
- append events to a stream log
- track consumer offsets
- update windowed stream features in the sharded replicated store

## Important Conceptual Layers

The project now has five main implemented layers:

### 1. Storage layer

- `KVStore`
- `WAL`
- `MemTable`
- `SSTables`
- compaction

This answers:

```text
How does one node store data correctly?
```

### 2. Replication layer

- `Node`
- `Cluster`

This answers:

```text
How do several nodes keep copies of the same shard?
```

### 3. Partitioning layer

- `HashRing`
- `ShardGroup`
- `ShardedCluster`

This answers:

```text
Which shard owns this key?
```

### 4. Batch layer

- `BatchEngine`
- `FeatureBatchJob`

This answers:

```text
How do we compute useful derived data from many records?
```

### 5. Stream layer

- `EventLog`
- `Producer`
- `Consumer`
- `OffsetStore`
- `TumblingWindow`
- `StreamFeatureProcessor`

This answers:

```text
How do we update features as new events arrive?
```

## Current Intended Topology

The current notes and examples use:

```text
RF = 3 = 1 leader + 2 followers per replicated group
```

That means:

- one shard owns a subset of keys
- that shard is stored on three replicas

## Verification Snapshot

At the current stage, the implemented system is validated by:

- storage tests
- replication tests
- sharding tests
- batch tests
- stream tests
- replication demo script
- batch demo script
- stream demo script

So this directory now documents the full implemented part of the course, and the remaining weeks are still intentionally blank until that code exists.
