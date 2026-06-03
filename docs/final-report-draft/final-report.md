# MLStore-Lite Final Report Draft

## 1. Introduction

Modern machine learning systems depend on data infrastructure that can store
features, update them from new events, and recover from failures. The goal of
MLStore-Lite is to build a small educational prototype of such a system. The
project is inspired by the distributed data-system concepts from *Designing
Data-Intensive Applications*, but keeps the implementation local and readable.

The project does not try to compete with production systems such as RocksDB,
Cassandra, Kafka, Spark, Flink, or managed ML platforms. I do not claim deep
practical knowledge of all of these frameworks. Instead, I use them as reference
points for understanding the architecture of data-intensive systems. The goal is
to build small versions of their central ideas so that the internal design
becomes easier to inspect: write-ahead logging, sorted-string tables,
replication, partitioning, batch processing, stream processing, observability,
and online model inference can all be studied in one code base.

The final system can run a small feature workflow end to end. Raw historical
events are converted into batch features, new events are appended to a stream
log, stream consumers update windowed features, and all feature values are
stored in a sharded replicated key-value store. The final extension serves those
features to a small model inference layer and logs predictions for inspection.

This project is also personal learning work. Coming from a mathematics
background and having worked with code for a bit less than two years, I wanted
to go deeper into software architecture rather than only use high-level
libraries. DDIA was useful because it explains why systems are shaped the way
they are: how data is stored, copied, partitioned, processed, and observed. In
future iterations of this repository, I would like to revisit the project with
the newer DDIA edition and add small implementations inspired by *System Design
Interview*.

## 2. Reading Scope and Project Method

The reading scope followed the course proposal and focused on selected parts of
*Designing Data-Intensive Applications* rather than the entire book. The second
edition of the book was released in 2026 by Martin Kleppmann and Chris
Riccomini. A future direction for this repository is to revisit the project with
the newer edition in more depth, especially the parts on cloud-native systems,
managed platforms, and operational tradeoffs.

The main DDIA reading and implementation mapping was:

| DDIA area | Project week | Implemented focus |
|---|---:|---|
| Chapter 3: Storage Engines | Week 1 | Write-ahead log, memtable, SSTable-like files, compaction, recovery |
| Chapter 5: Replication | Week 2 | Leader-follower replication, sync/async writes, replication lag, manual failover |
| Chapter 6: Sharding / Data Distribution | Week 3 | Hash-based partitioning, consistent hashing, virtual nodes, rebalancing, routing |
| Chapter 10: Batch Processing | Week 4 | Map-shuffle-reduce dataflow, retries, batch feature computation |
| Chapter 11: Stream Processing | Weeks 5-6 | Append-only event log, producers, consumers, offsets, tumbling-window features |

Several DDIA topics were intentionally not implemented deeply. Transactions,
consensus, automatic leader election, distributed commit protocols, real
network partitions, and production-grade distributed recovery are discussed only
as limitations or future work. This boundary was important because the project
was meant to make the main architecture understandable, not to reproduce a full
database, stream processor, or managed ML platform.

The implementation was AI-assisted. The code and documentation were developed
with Codex 5.5, Claude Sonnet 4.7, and Claude Opus 4.7 as programming and
writing assistants. I also experimented in some parts with local LLM models,
including Qwen models around 35B parameters. The AI tools were used for
iteration, explanation, implementation support, and debugging, while the project
scope, interpretation, and final report decisions remained part of the learning
process.

## 3. System Overview

MLStore-Lite is organized as a layered system. Each layer has a narrow
responsibility and builds on the layer below it:

```text
Storage engine
  -> Replication
  -> Sharding / partitioning
  -> Batch processing
  -> Stream processing
  -> Integration
  -> Evaluation and observability
  -> Online feature serving and model inference
```

This structure is useful because it separates concerns. The storage engine only
needs to know how one node persists key-value data. The replication layer only
needs to know how several nodes keep copies of the same data. The sharding layer
only decides which replicated group owns a key. Batch and stream processing then
use the sharded store without needing to understand the lower-level storage
details. The AI layer is the final consumer of the stored features.

## 4. Storage Engine

The storage engine answers the question:

```text
How does one node store data durably?
```

It consists of:

- a write-ahead log
- an in-memory table
- immutable SSTable files
- compaction

When a key is written, the value is first appended to the write-ahead log. This
means the operation can be recovered even if the process crashes before the
in-memory data is flushed to disk. The in-memory table keeps recent writes fast.
When it grows large enough, it is flushed into an SSTable file. SSTables are
immutable sorted files, which makes reads and merges more predictable.
Compaction later combines SSTables and removes overwritten values.

This is a simplified log-structured storage engine. The same broad idea appears
in systems such as LevelDB and RocksDB, although production engines add many
optimizations such as bloom filters, compression, concurrency control, and more
advanced compaction strategies.

## 5. Replication

The replication layer answers the question:

```text
How can the system keep multiple copies of the same data?
```

MLStore-Lite uses a leader-follower model. Each replicated group contains one
leader and two followers, giving a replication factor of three.

Writes go to the leader. The leader stores the write locally and forwards it to
followers. Reads are served through the current leader in the implemented
interface. The project also supports manual failover, where a follower can be
promoted to leader after a failure experiment.

Replication improves fault tolerance because one physical copy is no longer the
only place where data exists. In this prototype the replicas are local objects
and directories, not separate networked machines. This keeps the focus on the
data-system concept rather than on networking.

## 6. Sharding and Partitioning

Replication creates copies of the same data. Sharding divides different keys
across different replicated groups.

The sharding layer answers:

```text
Which shard owns this key?
```

MLStore-Lite uses consistent hashing for routing. A key is hashed onto a ring,
and the next shard on the ring owns that key. This means keys can be distributed
without manually assigning ranges such as `users 1-1000 go to shard A`. When a
shard is added, only part of the key space needs to move.

In the implemented topology, each shard is itself a replicated group with
replication factor three. Therefore a shard is not just one file or one Python
object. It is a logical partition of the key space, backed by multiple replica
nodes.

## 7. Batch Processing

The batch layer answers the question:

```text
How can raw historical records be turned into useful derived data?
```

In MLStore-Lite, the derived data are machine-learning-style features.

The batch engine follows a small MapReduce pattern:

```text
map -> shuffle -> reduce
```

The map step reads one input event and emits intermediate key-value pairs. The
shuffle step groups intermediate values by feature key. The reduce step combines
the grouped values into final feature values. For example, several click events
for the same user can become a single click-count feature.

The implemented batch feature job computes:

- per-user event count
- per-user click count
- per-user purchase count
- per-user total purchase amount

The results are written back into the sharded replicated store using keys such
as:

```text
feature:user:42:click_count
```

This mirrors the role of batch systems such as MapReduce and Spark, but at a
small local scale.

## 8. Stream Processing and Integration

Batch processing is useful for historical data, but many ML systems also need
fresh features from recent events. The stream layer answers:

```text
How can new events update derived data incrementally?
```

MLStore-Lite implements:

- a small append-only event log
- producers
- consumers
- an offset store
- tumbling windows
- a stream feature processor

Producers append events to the log. Consumers read from the log and track their
position using offsets. The processor groups events into fixed-size windows and
writes updated features into the same sharded replicated store used by the batch
layer.

This is similar in spirit to Kafka and stream processors such as Flink or Kafka
Streams. Kafka provides the durable distributed event log, while Flink and Kafka
Streams provide continuous computations over event streams. MLStore-Lite keeps a
small local version of the same idea: new events are appended, consumed, grouped,
and converted into feature updates.

The integration layer connects all previous components into one object:

```text
MLStoreLiteSystem
```

This object creates the sharded replicated store, the batch feature job, the
event log, producer, consumer, offset store, and stream processor. Its purpose is
not to hide the architecture, but to make the whole prototype runnable without
manually wiring every class each time.

The integrated system supports this workflow:

1. Compute batch features from historical events.
2. Produce new events into the stream log.
3. Process stream events into windowed features.
4. Read features from the sharded replicated store.
5. Inspect shard distribution and replica status.

This gives the project an end-to-end ML infrastructure story: raw events become
features, and the features are stored in a distributed-system-inspired storage
backend.

## 9. Evaluation and Observability

The evaluation layer adds local observability. In this project, observability
means:

- structured logs
- timing measurements
- reproducible experiment records

The goal is not to build a monitoring platform. The goal is to make the
prototype inspectable.

The Week 8 evaluation script builds the integrated system and measures:

- batch feature computation time
- stream event production time
- stream processing time
- feature read latency
- key distribution across shards

Each measurement is written to a JSON-lines file with:

- experiment name
- metric
- value
- unit
- timestamp
- parameters

The parameters include the number of events, number of shards, and replication
factor. This is important for reproducibility: a runtime number is more
meaningful when the conditions that produced it are also recorded.

The evaluation script also emits structured JSON logs. A structured log is more
useful than plain text because it can be parsed by other tools. For example, the
system can log that a measurement was recorded together with the operation name,
elapsed time, and output count.

## 10. Online Feature Serving and Model Inference

The final extension adds a small online inference layer. This layer uses the
features computed by the batch and stream processors and serves them to a
deterministic purchase-intent model.

The final prediction pipeline is:

```text
events
  -> batch features
  -> stream/window features
  -> sharded replicated feature store
  -> online feature server
  -> purchase intent model
  -> prediction log
```

The feature server reads expected user features from MLStore-Lite, including
historical batch features and recent windowed stream features. It also records
whether expected inputs are missing.

The model uses the feature values to produce:

- purchase probability
- confidence
- label
- warnings

Example prediction:

```json
{
  "user_id": "0",
  "model_version": "purchase-intent-v1",
  "purchase_probability": 0.9953,
  "confidence": 1.0,
  "label": "likely_to_purchase",
  "warnings": []
}
```

If features are missing, the model lowers confidence and records warnings:

```json
{
  "user_id": "999",
  "purchase_probability": 0.0989,
  "confidence": 0.32,
  "label": "uncertain",
  "warnings": [
    "missing_event_count",
    "missing_click_count",
    "missing_purchase_count",
    "missing_total_purchase_amount",
    "no_recent_stream_activity"
  ]
}
```

This is intentionally not a large model-training system. The purpose is to show
the role of the data infrastructure in model serving:

```text
features must be computed, stored, served, checked, and logged.
```

Predictions are written to a JSON-lines log with the user id, model version,
input features, prediction probability, confidence, label, and warnings. This
connects the AI extension back to MLOps: model outputs should be traceable and
debuggable, not just returned and forgotten.

## 11. Comparison With Production Tools

MLStore-Lite is a teaching prototype, so the comparison with production systems
is conceptual rather than a performance benchmark.

| MLStore-Lite layer | Production reference | Shared idea |
|---|---|---|
| Storage engine | RocksDB / LevelDB | WAL, memtable, SSTables, compaction |
| Sharding and replication | Cassandra | Partitioned key space, replicated data |
| Event log | Kafka | Append-only events, producers, consumers, offsets |
| Batch processing | Spark / MapReduce | Map, shuffle, reduce over finite data |
| Stream processing | Flink / Kafka Streams | Continuous event processing and windowed state |
| Integrated workflow | Databricks / managed platforms | End-to-end data and ML infrastructure |
| Inference extension | Feature stores / model serving systems | Online feature retrieval and prediction logging |

The main difference is scale and operational complexity. Production tools run
across real machines, handle concurrent users, recover from many failure modes,
and optimize for performance. MLStore-Lite runs locally and focuses on making
the core ideas understandable.

## 12. Limitations

The most important limitation is that the project is local. Nodes are Python
objects and directories, not independent networked processes.

The project does not include:

- real network transport
- automatic leader election
- background repair
- distributed query execution
- production-grade monitoring
- model training
- model registry
- HTTP model serving API
- a deep implementation of DDIA topics such as transactions and consensus

The evaluation is also intentionally small. The measurements are useful for
checking that the system runs and for discussing relative behavior, but they are
not benchmarks against real systems. The synthetic workloads are small enough to
keep the project readable and runnable on a laptop.

These limitations are acceptable because the goal is educational. The project
prioritizes clarity of architecture over production completeness.

## 13. Conclusion

MLStore-Lite implements a compact data infrastructure prototype for ML-style
features. The project starts from a single-node storage engine and gradually
adds replication, sharding, batch processing, stream processing, integration,
observability, and online model inference.

The final result shows how raw events can become derived feature values, and how
those values can be stored in a sharded replicated backend, served to a model,
and logged as predictions.

The project also shows why evaluation and observability matter. Once a system
has several layers, it needs logs, measurements, and reproducible records to be
understandable.

The final architecture can be summarized as:

```text
events -> features -> feature store -> online inference -> prediction logs
```
