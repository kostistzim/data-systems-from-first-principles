# MLStore-Lite: Week 7 Notes
## Full System Integration and Basic Evaluation

## 1. Why Integration Comes After The Individual Layers

Weeks 1-6 implemented separate system layers:

- storage
- replication
- sharding
- batch processing
- stream processing

Week 7 connects them into one usable MLStore-Lite system.

The question changes from:

```text
Can each piece work by itself?
```

to:

```text
Can the pieces work together as one data platform?
```

That is the purpose of the integration layer.

---

## 2. Architecture After Week 7

The integrated system wires together:

```text
Batch events
  -> FeatureBatchJob
  -> ShardedCluster

Stream events
  -> Producer
  -> EventLog
  -> Consumer
  -> StreamFeatureProcessor
  -> ShardedCluster

ShardedCluster
  -> ShardGroup
  -> Cluster
  -> Node
  -> KVStore
```

This means batch and stream feature computation now write into the same sharded replicated store.

The lower layers still keep their responsibilities:

- `KVStore`: local storage
- `Cluster`: replication
- `ShardedCluster`: partitioning
- `FeatureBatchJob`: batch feature computation
- `StreamFeatureProcessor`: fresh windowed feature updates

---

## 3. What Was Implemented

The Week 7 implementation includes:

- `MLStoreLiteSystem`
- `create_mlstore_lite_system`
- an end-to-end integration demo
- a simple benchmark script
- integration tests

The system builder creates:

- two shards
- RF = 3 per shard
- batch feature job
- event log
- producer
- consumer
- offset store
- stream feature processor

So demos and tests no longer need to manually wire every layer.

---

## 4. The Integrated System Object

`MLStoreLiteSystem` is a convenience layer around the whole project.

It exposes methods like:

```text
run_batch_features(events)
produce_event(event)
produce_events(events)
process_stream_events(max_records)
get_feature(key)
failover_shard(shard_id)
status()
```

This is not a new storage engine.

It is the orchestration object that holds the already implemented parts together.

That distinction matters:

- storage still happens in `KVStore`
- replication still happens in `Cluster`
- sharding still happens in `ShardedCluster`
- batch and stream still compute features
- the integration layer just makes them easier to use together

---

## 5. End-To-End Demo

The Week 7 integration demo runs this flow:

1. create the full MLStore-Lite system
2. run a batch feature job
3. produce stream events
4. process stream events
5. manually fail over one shard
6. continue processing after failover
7. print final system status

This demonstrates that the system is now more than separate weekly exercises.

It can run a small end-to-end feature pipeline.

---

## 6. Manual Failure Experiment

The integration layer supports a simple controlled failover:

```text
failover_shard("shard-a")
```

This promotes the most up-to-date follower to leader for that shard.

The goal is not to implement automatic leader election.

The goal is to show that:

- shards are replicated groups
- a follower can be promoted
- writes can continue after manual failover

This keeps the experiment aligned with the course scope.

---

## 7. Basic Benchmarking

The Week 7 benchmark script measures simple elapsed times for:

- batch feature computation
- producing stream events
- processing stream events
- reading a sample feature

This is intentionally small.

The point is not to claim production performance.

The point is to create measurements that can support discussion in the final report.

Useful questions include:

- does sync replication make writes slower?
- how does batch processing time grow with input size?
- how quickly can stream events be processed locally?
- how are feature keys distributed across shards?

---

## 8. What This Layer Does Not Try To Solve

Week 7 does not implement:

- automatic cluster management
- real node processes
- network transport
- automatic failover
- production-grade benchmarking
- deployment automation

Those would make the project much larger.

The integration layer is meant to show how the implemented concepts compose.

---

## 9. Code Map

The main Week 7 implementation lives in:

- `src/mlstore_lite/integration/system.py`
- `src/mlstore_lite/experiments/week7_integration_demo.py`
- `src/mlstore_lite/experiments/week7_benchmark.py`
- `tests/test_integration.py`

What each file does:

- `system.py`: constructs and exposes the full integrated MLStore-Lite system
- `week7_integration_demo.py`: end-to-end demo across batch, stream, sharding, replication, and storage
- `week7_benchmark.py`: simple timing measurements
- `test_integration.py`: verifies the integrated behavior

---

## 10. How This Week Is Verified

The main verification is:

- `tests/test_integration.py`

The tests verify:

- batch and stream features can both be written through the integrated system
- consumer offsets advance after stream processing
- manual failover does not prevent later stream writes
- system status reports shard and replica information

The runnable demos are:

```text
python -m mlstore_lite.experiments.week7_integration_demo
python -m mlstore_lite.experiments.week7_benchmark
```

---

## 11. Short Summary

Week 7 turns MLStore-Lite from a set of implemented layers into one coherent prototype.

The core idea is:

```text
batch + stream feature computation
    -> sharded replicated feature store
    -> local durable storage
```

This prepares the project for Week 8: evaluation, comparison with industry tools, and final report writing.
