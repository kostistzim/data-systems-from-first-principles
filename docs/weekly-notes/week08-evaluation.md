# MLStore-Lite: Week 8 Notes
## Evaluation, Observability, and Comparison With Industry Tools

## 1. Why Week 8 Is Different

Weeks 1-7 built the system itself:

- Week 1: local storage
- Week 2: replication
- Week 3: partitioning / sharding
- Week 4: batch processing
- Week 5-6: stream processing
- Week 7: full integration

Week 8 does not add another distributed-systems subsystem.

Instead, it asks:

```text
How do we inspect, measure, debug, and explain the system we built?
```

That is where evaluation and MLOps observability enter the project.

The short story is:

```text
DDIA built the internals.
MLOps observability helps us inspect and evaluate those internals.
```

This matters because building a system is only half of the engineering problem.
The other half is being able to answer questions like:

- did the system do what I expected?
- how long did an operation take?
- where did this output come from?
- can I reproduce the measurement later?
- what are the limitations compared with real production tools?

Week 8 adds a small local observability layer for those questions.

---

## 2. What Observability Means In This Project

In large production systems, observability often means metrics dashboards, log
aggregation, traces, alerts, profiling tools, and experiment tracking systems.

MLStore-Lite keeps the idea much smaller and local.

Here, observability means:

- structured logs for important events
- simple timing measurements for operations
- JSON-lines experiment records that can be inspected later
- a repeatable evaluation script
- notes that compare the prototype to real systems

The project intentionally does not use:

- Prometheus
- Grafana
- MLflow
- Weights & Biases
- cloud logging
- distributed tracing

Those are useful tools, but adding them would change the scope of the project.
The goal here is to show the concepts with standard Python only.

---

## 3. Architecture After Week 8

The system architecture now looks like this:

```text
Evaluation script
  -> Observability helpers
  -> MLStoreLiteSystem
  -> Batch layer
  -> Stream layer
  -> ShardedCluster
  -> Cluster
  -> Node
  -> KVStore
```

The observability layer sits beside the system.

It does not store user features.
It does not replicate data.
It does not choose shards.
It does not process events.

Instead, it records what happens when those layers run.

That distinction is important:

- storage is the thing being evaluated
- replication is the thing being evaluated
- sharding is the thing being evaluated
- batch and stream are the things being evaluated
- observability is the notebook that records the measurements

---

## 4. What Was Implemented

Week 8 adds:

- `src/mlstore_lite/observability/logging.py`
- `src/mlstore_lite/observability/profiling.py`
- `src/mlstore_lite/observability/experiment_log.py`
- `src/mlstore_lite/experiments/week8_evaluation.py`
- `tests/test_observability.py`

The implementation stays dependency-free.

It uses only the Python standard library:

- `logging`
- `json`
- `time.perf_counter`
- local files

---

## 5. Structured Logging

The structured logger writes log messages as JSON objects.

A normal text log might look like:

```text
evaluation started
```

A structured log looks more like:

```json
{"batch_events": 250, "level": "INFO", "message": "week8_evaluation_started", "stream_events": 250}
```

This is easier to search, filter, and parse.

For example, a later script could read logs and ask:

```text
Show me all records where message = "measurement_recorded".
```

In this project, logs go to stdout. That keeps the implementation simple while
still showing the MLOps idea:

```text
important events should be machine-readable, not only human-readable.
```

---

## 6. Profiling

Profiling means measuring where time is spent.

Production profiling can be very detailed. It might inspect CPU samples,
memory allocation, network latency, or function call stacks.

MLStore-Lite uses a smaller version:

```text
start timer
run operation
stop timer
record elapsed seconds
```

The implementation uses `time.perf_counter()` because it is appropriate for
measuring short elapsed durations.

The evaluation script measures:

- batch feature computation time
- stream event production time
- stream processing time
- feature read latency

These measurements are not production benchmarks.

They are local experiments that help explain system behavior and create data
for the final report.

---

## 7. Experiment Logging

The experiment log writes one JSON object per line.

This format is called JSON-lines.

Example record:

```json
{"experiment": "batch_feature_runtime", "metric": "elapsed_time", "unit": "seconds", "value": 0.012}
```

Each record contains:

- `timestamp`
- `experiment`
- `metric`
- `value`
- `unit`
- `parameters`

The `parameters` field matters because a measurement without context is weak.

For example, this number is not very useful by itself:

```text
batch runtime = 0.01 seconds
```

This is more useful:

```text
batch runtime = 0.01 seconds
with 250 input events, 2 shards, RF = 3
```

That is the reproducibility idea from MLOps:

```text
record not just the result, but also the conditions that produced the result.
```

---

## 8. The Week 8 Evaluation Script

The main Week 8 script is:

```text
PYTHONPATH=src python3 src/mlstore_lite/experiments/week8_evaluation.py
```

It does the following:

1. creates a fresh local demo directory
2. builds the integrated MLStore-Lite system
3. creates synthetic batch events
4. creates synthetic stream events
5. runs the batch feature workflow
6. produces events into the stream log
7. processes stream events into windowed features
8. reads one feature value
9. records shard key distribution
10. writes evaluation records to JSON-lines
11. prints a short summary

The output file is:

```text
demo_data/week8/evaluation/results.jsonl
```

This file is generated output. It is useful for local inspection and report
drafting, but it does not need to be committed.

---

## 9. What Is Being Evaluated

The Week 8 script evaluates the already implemented layers.

### 9.1 Storage

Storage is tested indirectly when features are written and read.

The relevant question is:

```text
Can computed feature values be persisted and retrieved?
```

In MLStore-Lite, this goes through:

```text
KVStore -> WAL -> MemTable -> SSTable
```

### 9.2 Replication

Replication is tested indirectly because each shard is backed by a replicated
cluster with RF = 3.

When the evaluation writes features, each write goes to a leader and then to
followers.

The relevant question is:

```text
Can the system write through replicated shard groups?
```

### 9.3 Sharding

Sharding is evaluated through key distribution.

After batch and stream writes, the script records how many keys live on each
shard.

The relevant question is:

```text
Are feature keys being routed across shards instead of all going to one place?
```

### 9.4 Batch Processing

Batch processing is evaluated by running a finite set of input events through
the feature job.

The relevant question is:

```text
How long does it take to compute historical aggregate features?
```

### 9.5 Stream Processing

Stream processing is evaluated by producing events and consuming them into
windowed feature updates.

The relevant question is:

```text
Can new events update features incrementally after the batch job has run?
```

### 9.6 Integration

Integration is evaluated because all of these operations run through one system
object.

The relevant question is:

```text
Can storage, replication, sharding, batch, and stream work together?
```

---

## 10. Comparison With Industry Tools

MLStore-Lite is a teaching prototype. It intentionally implements small,
readable versions of ideas that production systems implement at much larger
scale.

### 10.1 RocksDB / LevelDB

RocksDB and LevelDB are storage engines based on log-structured merge tree
ideas.

They are comparable to MLStore-Lite's storage layer:

- WAL
- MemTable
- SSTables
- compaction

The difference is that RocksDB and LevelDB are highly optimized and battle
tested. They handle many details MLStore-Lite does not handle, such as advanced
compaction strategies, compression, bloom filters, concurrency, and careful
disk performance tuning.

MLStore-Lite is useful because it makes the basic shape visible.

### 10.2 Cassandra

Cassandra is closer to the sharding and replication parts of the project.

It partitions keys across nodes and stores replicas for fault tolerance.

MLStore-Lite has:

- consistent hashing
- shard groups
- RF = 3
- leader/follower replication

Cassandra is much more advanced. It has real networked nodes, membership
management, tunable consistency levels, repair mechanisms, gossip, and automatic
handling of node failures.

MLStore-Lite keeps these ideas local and explicit.

### 10.3 Kafka

Kafka is comparable to the stream event log.

Both systems have the idea of:

- append-only events
- producers
- consumers
- offsets

Kafka is distributed, durable, partitioned, replicated, and designed for very
high throughput.

MLStore-Lite's event log is local and simple. Its value is that it makes the
event-log abstraction understandable before adding production complexity.

### 10.4 Spark / MapReduce

Spark and MapReduce are comparable to the batch layer.

MLStore-Lite uses the same conceptual pattern:

```text
map -> shuffle -> reduce
```

Production batch systems distribute work across many machines, recover failed
tasks, optimize execution plans, and manage large datasets.

MLStore-Lite runs locally. It is meant to show the dataflow idea clearly.

### 10.5 Flink / Kafka Streams

Flink and Kafka Streams are comparable to the stream processing layer.

They process events continuously and maintain derived state such as windows,
counts, and aggregations.

MLStore-Lite includes:

- event production
- event consumption
- offsets
- tumbling windows
- feature updates

Production stream processors add distributed execution, checkpoints, watermarks,
event-time semantics, fault tolerance, and scaling.

MLStore-Lite keeps the core idea:

```text
new events can update derived features continuously.
```

### 10.6 Databricks / Managed ML Platforms

Databricks and managed ML platforms are closer to an end-to-end version of this
project.

They combine:

- storage
- batch processing
- stream processing
- notebooks
- model training
- experiment tracking
- observability
- deployment tools

MLStore-Lite is not trying to replace those systems.

It is a compact learning project that shows the internal building blocks behind
some of the same workflows.

---

## 11. Limitations

The Week 8 evaluation has important limitations:

- it runs on one machine
- nodes are local objects, not separate processes
- there is no real network
- measurements are small and synthetic
- timings depend on the local machine
- there is no automatic dashboard
- there is no distributed tracing
- there is no production-grade load testing
- generated experiment data is not versioned by default

These limitations are acceptable for the project scope.

The purpose is not to claim production performance.

The purpose is to demonstrate that the system can be inspected, measured, and
explained.

---

## 12. Lessons Learned

The main lesson from Week 8 is that observability is not only something added
after a system becomes large.

Even a small prototype benefits from:

- clear logs
- repeatable experiments
- timing measurements
- explicit parameters
- written comparison against real tools

This also helps the final report because it turns the project from:

```text
I implemented several files.
```

into:

```text
I built a layered data-system prototype and evaluated how the layers behave.
```

That is a much stronger story.

---

## 13. Code Map

The main Week 8 implementation lives in:

- `src/mlstore_lite/observability/logging.py`
- `src/mlstore_lite/observability/profiling.py`
- `src/mlstore_lite/observability/experiment_log.py`
- `src/mlstore_lite/experiments/week8_evaluation.py`
- `tests/test_observability.py`

What each file does:

- `logging.py`: creates a small JSON logger for structured logs
- `profiling.py`: measures elapsed wall-clock time for one operation
- `experiment_log.py`: appends reproducible experiment records to JSON-lines
- `week8_evaluation.py`: runs the full system and records measurements
- `test_observability.py`: verifies the observability helpers

---

## 14. How This Week Is Verified

The main verification commands are:

```text
/opt/anaconda3/bin/python3 -m pytest -q
PYTHONPYCACHEPREFIX=/tmp/mlstore-pycache python3 -m compileall src tests
PYTHONPATH=src python3 src/mlstore_lite/experiments/week8_evaluation.py
```

The expected result is:

- all tests pass
- source files compile
- the Week 8 evaluation script prints a readable summary
- `demo_data/week8/evaluation/results.jsonl` is created

The JSON-lines file can be used as raw evidence in the final report.
