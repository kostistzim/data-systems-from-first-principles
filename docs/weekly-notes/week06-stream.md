# MLStore-Lite: Week 6 Notes
## Windowed Stream Feature Processing

## 1. Why Windowing Is Needed

Week 5 created an event log and consumer offsets.

Week 6 turns those events into continuously updated features.

The challenge is that streams do not naturally end.

With batch processing, it is clear where the input begins and ends.

With stream processing, events keep arriving.

So we often define windows:

```text
process events from time 0-59
then time 60-119
then time 120-179
```

That gives the stream processor finite pieces of an infinite input.

---

## 2. Tumbling Windows

This project implements tumbling windows.

A tumbling window is:

- fixed size
- non-overlapping
- based on event timestamps

With a 60-second window:

```text
timestamp 10 -> window 0
timestamp 59 -> window 0
timestamp 60 -> window 60
timestamp 119 -> window 60
```

The window start becomes part of the feature key.

Example:

```text
feature:user:42:window:0:click_count
feature:user:42:window:60:click_count
```

This keeps features for different time windows separate.

---

## 3. Architecture After Week 6

The full stream feature path is:

```text
Producer
  ↓
EventLog
  ↓
Consumer
  ↓
StreamFeatureProcessor
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

This connects stream processing to everything implemented earlier.

The stream layer reads events.

The sharding layer routes feature keys.

The replication layer copies each shard's writes.

The storage layer persists each replica locally.

---

## 4. What Was Implemented

The Week 6 implementation includes:

- tumbling window assignment
- stream feature aggregation
- incremental feature updates into `ShardedCluster`
- consumer offset commits after successful processing
- a runnable stream demo

The stream processor computes:

- event count per user per window
- click count per user per window
- purchase count per user per window
- total purchase amount per user per window

Feature keys look like:

```text
feature:user:42:window:0:click_count
feature:user:42:window:60:total_purchase_amount
```

---

## 5. How Processing Works

When the stream processor runs:

1. consumer polls events from its committed offset
2. each event is assigned to a tumbling window
3. feature deltas are computed
4. deltas are added to existing feature values in MLStore-Lite
5. updated feature values are written through `ShardedCluster`
6. the consumer commits the next offset

The word "delta" means change.

Example:

```text
new click event -> add 1 to click_count
```

If the current stored value is `1`, the updated value becomes `2`.

---

## 6. Batch vs Stream In This Project

Batch processing:

```text
process a finite dataset all at once
```

Stream processing:

```text
process new events as they appear
```

They can compute similar features, but their role is different.

Batch is good for historical recomputation.

Stream is good for freshness.

For ML infrastructure, this distinction matters because a model may need both:

- stable historical features
- fresh real-time features

---

## 7. Processing Semantics

This implementation commits offsets after writing features.

That gives a simple at-least-once style behavior:

- if processing succeeds, the offset advances
- if processing fails before commit, the same events may be read again

This project does not implement exactly-once semantics.

That is intentional. Exactly-once stream processing requires more machinery than fits this course scope.

The important lesson is that offset commits are part of correctness, not just bookkeeping.

---

## 8. What This Layer Does Not Try To Solve

This Week 6 implementation does not include:

- exactly-once processing
- late-event handling
- watermarks
- sliding windows
- distributed stream partitions
- checkpointed operator state

Those are real stream-processing topics, but the current implementation focuses on the core event-log, offset, and window concepts.

---

## 9. Code Map

The main Week 6 implementation lives in:

- `src/mlstore_lite/stream/windows.py`
- `src/mlstore_lite/stream/processor.py`
- `src/mlstore_lite/experiments/week5_stream_demo.py`
- `tests/test_stream.py`

What each file does:

- `windows.py`: assigns timestamps to tumbling windows
- `processor.py`: reads events, aggregates features, writes into MLStore-Lite, and commits offsets
- `week5_stream_demo.py`: runnable demo for the full stream path
- `test_stream.py`: verifies event logs, offsets, windowing, and stream feature writes

---

## 10. How This Week Is Verified

The main verification is:

- `tests/test_stream.py`

The tests verify:

- tumbling-window assignment
- feature writes into the sharded replicated store
- consumer offset advancement
- incremental updates across multiple processing batches
- replica agreement inside each shard

The runnable demo is:

```text
python -m mlstore_lite.experiments.week5_stream_demo
```

It shows events being produced, offsets advancing, features being updated, and shard replica status.

---

## 11. Short Summary

Week 6 completes the stream-processing layer for MLStore-Lite.

The core idea is:

```text
event log -> consumer offsets -> windowed aggregation -> sharded replicated feature store
```

This gives the project both batch and stream feature computation.

Batch provides historical feature computation.

Stream provides fresher feature updates as new events arrive.
