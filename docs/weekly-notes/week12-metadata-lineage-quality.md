# Week 12: Metadata, Lineage, and Data Quality

Week 12 is a final inspection layer.

The earlier weeks made MLStore-Lite able to store, replicate, shard, process,
and serve features. Week 12 asks three practical questions:

```text
What does this feature mean?
Was this input event valid?
Which data was used to make this prediction?
```

This does not make the system more distributed. It makes the system easier to
understand and debug.

## 1. Feature Registry

The feature registry is a small local catalog:

```text
src/mlstore_lite/catalog/
```

It stores metadata such as:

```text
feature name
key pattern
source layer
value type
description
models that use it
```

For example, the key:

```text
feature:user:42:click_count
```

is just a string in the storage engine. The registry explains that it means:

```text
Number of historical click-like events observed for a user.
```

This is useful because feature stores are not only about storing values. They
also need a place where people can understand what those values mean.

## 2. Data Quality

The quality layer is here:

```text
src/mlstore_lite/quality/
```

It validates simple event rules:

```text
user_id must exist
event_type must be known
timestamp must exist for stream-style events
amount must be numeric and non-negative
```

Invalid events are reported and skipped in demos. Valid events continue through
the pipeline.

This is a small version of a common production idea: bad data should be noticed
before it silently becomes bad features.

## 3. Lineage

The lineage layer is here:

```text
src/mlstore_lite/lineage/
```

It writes JSON-lines records that explain prediction traces.

A prediction lineage record can say:

```text
user_id = 0
model_version = purchase-intent-v1
input_feature_keys = feature:user:0:click_count, ...
output_keys = prediction:user:0:purchase_probability, prediction:user:0:label
missing_features = []
```

This helps answer:

```text
Why did the model make this prediction?
Which feature keys did it read?
Was anything missing?
```

## Demo

Run:

```bash
make week12
```

The demo intentionally includes a few bad events so the quality report has
something to catch.

Generated files:

```text
demo_data/week12/metadata_lineage_quality/quality_report.json
demo_data/week12/metadata_lineage_quality/lineage.jsonl
demo_data/week12/metadata_lineage_quality/predictions.jsonl
```

## How This Fits The Architecture

The final flow becomes:

```text
raw events
  -> data quality checks
  -> batch / stream processing
  -> feature registry explains feature meanings
  -> sharded replicated feature store
  -> model inference / recommender
  -> prediction log
  -> lineage log
```

The important idea is simple:

```text
Quality checks protect the input.
The registry explains the features.
Lineage explains the prediction.
```

## What This Does Not Do

This is not a full governance platform. It does not include permissions,
approval workflows, central metadata servers, or enterprise data catalogs.

It is a small local version of the same architecture idea, enough to make the
project easier to inspect and explain.
