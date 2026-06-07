# MLStore-Lite: Week 10 Notes
## Local Scaling Experiments and Cloud Architecture

## 1. Why This Week Exists

Weeks 1-9 built a local feature platform:

```text
events -> features -> feature store -> online inference -> prediction logs
```

Week 10 does not add a new core system layer.

Instead, it asks:

```text
What does scaling mean for this architecture?
```

The answer is split into two parts:

- local experiments that can run on a laptop
- a cloud architecture sketch for future work

This distinction matters. MLStore-Lite has scaling concepts such as sharding,
replication, batch processing, and stream processing, but it is not a production
distributed system.

---

## 2. Workload Scaling Experiment

The workload scaling experiment runs the integrated system with increasing event
counts:

```text
250 events
2500 events
10000 events
```

For each workload, it measures:

- batch feature runtime
- stream event production runtime
- stream processing runtime
- feature read latency
- total stored feature keys
- shard key distribution

This is not a production benchmark. It is a local experiment that helps answer:

```text
How does this Python prototype behave as the input size grows?
```

Run it with:

```text
PYTHONPATH=src python3 src/mlstore_lite/experiments/week10_scaling_experiment.py
```

Generated results:

```text
demo_data/week10/scaling/results.jsonl
```

---

## 3. Shard Hotspot Experiment

The hotspot experiment compares two workloads:

- balanced workload: events spread across many users
- hotspot workload: most events target one user

The goal is to show that partitioning is not only about the number of stored
keys. It is also about request distribution.

If many requests target the same key or user, the shard that owns that key may
receive much more traffic than other shards.

Run it with:

```text
PYTHONPATH=src python3 src/mlstore_lite/experiments/week10_hotspot_experiment.py
```

Generated results:

```text
demo_data/week10/hotspot/results.jsonl
```

This connects directly to DDIA's partitioning discussion:

```text
hashing can spread keys, but it cannot automatically remove all workload skew.
```

---

## 4. Cloud Architecture Sketch

The cloud design document is:

```text
docs/cloud-architecture.md
```

It maps the local MLStore-Lite layers to possible cloud or production-style
systems:

- Kafka / PubSub / Kinesis for event ingestion
- Spark / Databricks / Beam for batch processing
- Flink / Kafka Streams / Dataflow for stream processing
- Cassandra / DynamoDB / Bigtable for distributed feature storage
- Feast or managed feature stores for online feature serving
- model serving endpoints for inference
- cloud logs, metrics, traces, or MLflow for observability

This is intentionally not implemented. It is included to clarify the difference
between:

```text
local architecture prototype
```

and:

```text
production cloud deployment
```

---

## 5. What Week 10 Does Not Do

Week 10 does not add:

- real distributed workers
- threads or multiprocessing
- Kafka
- Spark
- Flink
- Docker
- cloud SDKs
- HTTP APIs

Those could be future work, but adding them now would make the project harder
to understand and submit.

The purpose of Week 10 is to make scaling questions visible without expanding
the implementation too much.

---

## 6. How This Week Is Verified

Run:

```text
/opt/anaconda3/bin/python3 -m pytest -q
PYTHONPYCACHEPREFIX=/tmp/mlstore-pycache python3 -m compileall src tests
PYTHONPATH=src python3 src/mlstore_lite/experiments/week10_scaling_experiment.py
PYTHONPATH=src python3 src/mlstore_lite/experiments/week10_hotspot_experiment.py
```

Expected result:

- tests pass
- source files compile
- scaling experiment prints a compact table
- hotspot experiment prints balanced vs hotspot request counts
- JSON-lines results are generated under `demo_data/week10/`
