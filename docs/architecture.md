# MLStore-Lite Architecture

MLStore-Lite is a local educational prototype of a feature platform. It builds
from storage internals up to online model inference, a small sequential
recommender, and a final inspection layer for metadata, lineage, and data
quality.

## Layers

### 1. Storage

One node stores key-value data using a write-ahead log, memtable, SSTable-like
files, and compaction. This is the local durability foundation.

### 2. Replication

Several local nodes keep copies of the same data using leader-follower
replication. Writes go through the leader and are copied to followers.

### 3. Sharding

The key space is split across shards using consistent hashing. Each shard is a
replicated group, so sharding divides keys while replication keeps copies.

### 4. Batch Processing

Historical events are processed with a small MapReduce-style flow:

```text
map -> shuffle -> reduce
```

The batch job writes user features such as click counts and purchase totals into
the sharded replicated store.

### 5. Stream Processing

New events are appended to a local event log, consumed with offsets, grouped
into tumbling windows, and written back as windowed features.

### 6. Integration

`MLStoreLiteSystem` wires together storage, replication, sharding, batch, and
stream processing so the project can run as one prototype.

### 7. Evaluation and Observability

Week 8 adds structured logs, timing measurements, and JSON-lines experiment
records. These do not make the system distributed; they make it inspectable.

### 8. Online Feature Serving and Inference

The AI extension reads stored features through a `FeatureServer`, runs a small
`PurchaseIntentModel`, and writes predictions to a JSON-lines log.

The AI layer consumes the earlier weeks. It does not replace them:

```text
batch/stream features -> feature store -> feature server -> model prediction
```

### 9. Sequential Recommender

Week 11 adds an event-sequence model. Instead of only using feature counts, it
looks at ordered user histories such as:

```text
view laptop -> view laptop -> add_to_cart laptop
```

The implementation is a small Transformer-style model with token IDs,
embeddings, position signal, attention over recent events, and a scoring head.
It is intentionally local and dependency-light, but it shows how the earlier
data-system layers can feed a more realistic AI consumer.

### 10. Metadata, Lineage, and Data Quality

Week 12 adds a small inspection layer:

- a feature registry that explains what stored feature keys mean
- data quality checks that validate raw events before processing
- lineage records that show which feature keys were used for predictions

This layer does not make MLStore-Lite more distributed. It makes the system
easier to inspect and explain.

## Current Topology

The demos use:

- 2 shards: `shard-a`, `shard-b`
- RF = 3 per shard: 1 leader and 2 followers
- local directories as node storage
- no real network transport
- no automatic consensus or leader election
- no production deep-learning training stack
- no enterprise metadata or governance service

This keeps the implementation small enough to study while still showing the
core architecture of a larger data system.

## Scaling Thoughts

The project now includes local Week 10 experiments for workload scaling and
shard hotspots. These experiments do not make MLStore-Lite a production
distributed system, but they help show what would become important as workload
size and request skew grow.

The easiest way to see the full local pipeline is:

```text
make demo
```

For a possible cloud version of the same architecture, see:

```text
docs/cloud-architecture.md
```
