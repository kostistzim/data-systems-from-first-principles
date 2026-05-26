# MLStore-Lite: Week 5 Notes
## Event Logs, Producers, Consumers, and Offsets

## 1. Why Stream Processing Comes After Batch

Week 4 introduced batch processing:

```text
finite input records -> compute features -> write results
```

Week 5 starts the streaming side of the system.

The main difference is:

- batch assumes a bounded dataset
- streaming assumes events keep arriving over time

So batch asks:

```text
What can I compute from this dataset?
```

Streaming asks:

```text
What should I do as new events arrive?
```

This connects to DDIA Chapter 11.

---

## 2. The Core Idea: An Append-Only Event Log

The foundation of the stream layer is an append-only event log.

An event log is a sequence of records:

```text
offset 0 -> event A
offset 1 -> event B
offset 2 -> event C
```

The log does not update records in place.

New events are appended to the end.

This is similar in spirit to systems like Kafka, though this project implements only a small local version.

---

## 3. Important Terms

### 3.1 Event

An event is one fact that happened.

Example:

```text
{"user_id": "42", "event_type": "click", "timestamp": 10}
```

### 3.2 Producer

A producer writes events into the event log.

In MLStore-Lite, `Producer.send(event)` appends one event and returns its offset.

### 3.3 Consumer

A consumer reads events from the event log.

It does not remove events from the log.

It just reads from a position.

### 3.4 Offset

An offset is the event position in the log.

If a consumer has committed offset `3`, that means:

```text
I have processed events 0, 1, and 2.
Next time, start reading from 3.
```

### 3.5 Consumer Group

A consumer group is a named processing identity.

In this project, offsets are stored by group ID:

```text
feature-updater -> next offset 3
```

That lets the stream processor resume from where it left off.

---

## 4. Architecture After Week 5

The stream input side looks like:

```text
Producer
  ↓
EventLog
  ↓
Consumer
  ↓
OffsetStore
```

The `EventLog` stores the ordered sequence of events.

The `OffsetStore` stores how far each consumer group has processed.

This means the event log and the consumer offset are separate:

- the log remembers what happened
- the offset remembers how far one processor has read

That separation is a very important streaming idea.

---

## 5. What Was Implemented

The Week 5 implementation includes:

- append-only JSON-lines event log
- producer interface
- consumer interface
- file-backed offset store
- polling events from a committed offset
- committing consumer progress

The event log stores records like:

```json
{"offset":0,"event":{"user_id":"42","event_type":"click","timestamp":10}}
```

Offsets are stored separately in a small JSON file.

---

## 6. Why Offsets Matter

Offsets are how a streaming system remembers progress.

Without offsets, a consumer would not know whether an event was already processed.

Example:

```text
event log has offsets 0, 1, 2, 3, 4
consumer group has committed offset 3
```

That means the next poll starts at offset 3.

Events 0, 1, and 2 are considered already processed.

This is the bridge between a continuously growing log and repeatable processing.

---

## 7. What This Layer Does Not Try To Solve

This Week 5 implementation does not include:

- distributed partitions of the event log
- multiple consumers sharing partitions
- exactly-once processing
- retention policies
- compaction of the event log
- network transport

The purpose is to understand the log and offset model before adding stream feature computation.

---

## 8. Code Map

The main Week 5 implementation lives in:

- `src/mlstore_lite/stream/event_log.py`
- `src/mlstore_lite/stream/producer.py`
- `src/mlstore_lite/stream/consumer.py`
- `src/mlstore_lite/stream/offset_store.py`

What each file does:

- `event_log.py`: append and read ordered event records
- `producer.py`: small write interface over the event log
- `consumer.py`: reads from the committed group offset
- `offset_store.py`: persists consumer group offsets

---

## 9. How This Week Is Verified

The main verification is in:

- `tests/test_stream.py`

The tests verify:

- events append with increasing offsets
- consumers can read from offsets
- consumer groups can commit progress
- polling resumes from the committed offset

---

## 10. Short Summary

Week 5 adds the input side of stream processing.

The core idea is:

```text
events are appended to a log
consumers read from offsets
offsets track progress
```

This prepares the system for Week 6, where those events are converted into real-time features and written into MLStore-Lite.
