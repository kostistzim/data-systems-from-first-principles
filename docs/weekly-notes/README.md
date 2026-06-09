# MLStore-Lite Weekly Notes

This directory is the running implementation diary for the course project.

These notes are intentionally educational. They are meant to help a reader see
how the system was built layer by layer, not to sound like polished corporate
documentation.

At the moment, the code implementation is complete through:

- Week 1: storage engine
- Week 2: replication
- Week 3: partitioning / sharding
- Week 4: batch processing
- Week 5-6: stream processing
- Week 7: integration
- Week 8: evaluation
- Week 9: online feature serving and model inference
- Week 10: local scaling experiments and cloud architecture

## How To Read These Notes

If you are new to the repository, start with:

1. `../../README.md`
2. `../architecture.md`
3. `week01-storage.md`

After that, the weekly notes are meant to be read in order:

1. `week01-storage.md`
2. `week02-replication.md`
3. `week03-sharding.md`
4. `week04-batch.md`
5. `week05-stream.md`
6. `week06-stream.md`
7. `week07-integration.md`
8. `week08-evaluation.md`
9. `week09-ai-inference.md`
10. `week10-scaling-and-cloud.md`

That order follows the architecture of the system itself:

```text
single-node storage
    -> replicated node groups
    -> sharded distributed system
    -> batch feature computation
    -> stream feature updates
    -> integrated MLStore-Lite prototype
    -> local evaluation and observability
    -> online feature serving and model inference
    -> local scaling experiments and cloud design
```

## Run This First

The quickest way to check the project is:

```text
python -m pytest -q
python -m mlstore_lite.experiments.week8_evaluation
python -m mlstore_lite.experiments.week9_ai_inference_demo
python -m mlstore_lite.experiments.week10_scaling_experiment
python -m mlstore_lite.experiments.week10_hotspot_experiment
python -m mlstore_lite.experiments.final_demo
```

Use:

```text
docs/final-report-draft/final-report.md
```

as the report draft, and use this directory as the learning diary behind it.

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
- run batch and stream feature workflows through one integrated system object
- perform manual shard failover experiments
- run small local benchmarks
- write structured observability logs
- profile local operation runtimes
- record reproducible evaluation results as JSON-lines
- compare the prototype against production systems
- serve stored features to a small model inference layer
- log model predictions as JSON-lines records
- run local scaling and shard-hotspot experiments
- describe a possible cloud version of the architecture

## Important Conceptual Layers

The project now has eight main implemented layers plus one scaling/design extension:

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

### 6. Integration layer

- `MLStoreLiteSystem`
- `create_mlstore_lite_system`

This answers:

```text
How do all implemented layers work together as one prototype?
```

### 7. Evaluation and observability layer

- `get_logger`
- `timed`
- `ExperimentLog`
- `week8_evaluation.py`

This answers:

```text
How do we inspect, measure, and explain the system we built?
```

### 8. Online feature serving and model inference layer

- `FeatureServer`
- `PurchaseIntentModel`
- `InferenceService`
- `PredictionLog`

This answers:

```text
How can a model consume the features stored by MLStore-Lite?
```

### Week 10 scaling/design extension

- workload scaling experiment
- shard hotspot experiment
- cloud architecture sketch

This answers:

```text
How would this local prototype behave under larger or skewed workloads, and what would a cloud version look like?
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
- integration tests
- observability tests
- AI inference tests
- replication demo script
- batch demo script
- stream demo script
- integration demo script
- benchmark script
- Week 8 evaluation script
- Week 9 AI inference demo
- Week 10 scaling experiment
- Week 10 hotspot experiment

So this directory now documents the implemented course project through Week 10.
