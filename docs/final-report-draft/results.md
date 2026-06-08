# Representative Local Results

These results are from local demo runs on the development machine. They are
useful as evidence that the full system runs end to end, but they are not
production benchmarks.

The project uses local Python objects and local directories instead of real
networked nodes, so these numbers should be interpreted as laptop-scale
observations.

## Week 8 Evaluation

Command:

```bash
python -m mlstore_lite.experiments.week8_evaluation
```

Representative output:

```text
batch_feature_runtime: 0.011221s, items=55
stream_produce_runtime: 0.017159s, items=250
stream_process_runtime: 0.089418s, items=291
feature_read_latency: 0.000097s, items=1
```

Shard distribution after the run:

```text
{'shard-a': 167, 'shard-b': 179}
```

Interpretation:

- batch processing computed historical features from a finite event set
- stream processing updated windowed features from new events
- feature reads were local and very small-scale
- key distribution shows that feature keys were routed across both shards

The generated experiment log is:

```text
demo_data/week8/evaluation/results.jsonl
```

## Week 9 Online Inference

Command:

```bash
python -m mlstore_lite.experiments.week9_ai_inference_demo
```

Representative prediction output:

```text
user=0 probability=0.9953 confidence=1.0000 label=likely_to_purchase warnings=[]
user=1 probability=0.5125 confidence=1.0000 label=maybe_interested warnings=[]
user=2 probability=0.1483 confidence=0.5600 label=low_intent warnings=['missing_purchase_count', 'missing_total_purchase_amount', 'no_recent_stream_activity']
user=999 probability=0.0989 confidence=0.3200 label=uncertain warnings=['missing_event_count', 'missing_click_count', 'missing_purchase_count', 'missing_total_purchase_amount', 'no_recent_stream_activity']
```

Interpretation:

- user `0` has strong batch and recent stream activity, so the model gives a
  high purchase-intent probability
- user `1` has moderate activity, so the model returns `maybe_interested`
- user `2` has partial features but missing purchase/recent activity signals,
  so confidence is reduced
- user `999` has no stored features, so the prediction is marked `uncertain`

The generated prediction log is:

```text
demo_data/week9/ai/predictions.jsonl
```

## Report Use

These results can support the final report section on evaluation and
observability. The important point is not raw speed. The important point is that
the system can:

- compute features
- store them through sharding and replication
- process stream updates
- read features for inference
- log measurements and predictions

## Week 10 Workload Scaling

Command:

```bash
python -m mlstore_lite.experiments.week10_scaling_experiment
```

Representative output:

```text
events | batch_s | produce_s | process_s | read_s | keys | distribution
   250 | 0.010543 | 0.013034 | 0.089711 | 0.000102 |  346 | {'shard-a': 167, 'shard-b': 179}
  1000 | 0.022959 | 0.050308 | 1.221772 | 0.000088 | 1979 | {'shard-a': 948, 'shard-b': 1031}
  2500 | 0.058198 | 0.130416 | 7.259344 | 0.000064 | 5633 | {'shard-a': 2671, 'shard-b': 2962}
```

Interpretation:

- the experiment is local and single-process, so it is not a production scaling
  benchmark
- increasing the workload makes stream processing noticeably more expensive
- feature read latency remains small because the read is one local lookup
- shard key distribution stays reasonably balanced for this synthetic workload

The generated experiment log is:

```text
demo_data/week10/scaling/results.jsonl
```

## Week 10 Shard Hotspot Experiment

Command:

```bash
python -m mlstore_lite.experiments.week10_hotspot_experiment
```

Representative output:

```text
Workload: balanced
produce_s=0.048879
process_s=1.275851
event_pressure={'shard-a': 477, 'shard-b': 523}
key_distribution={'shard-a': 960, 'shard-b': 1040}
request_counts={'shard-a': 1920, 'shard-b': 2080}

Workload: hotspot
produce_s=0.051197
process_s=0.141293
event_pressure={'shard-a': 379, 'shard-b': 621}
key_distribution={'shard-a': 218, 'shard-b': 216}
request_counts={'shard-a': 436, 'shard-b': 432}
```

Interpretation:

- `event_pressure` estimates where raw events would route before aggregation
- `request_counts` shows actual store requests after the stream processor
  aggregates events into feature deltas
- the hotspot workload sends more raw event pressure toward `shard-b`
- the final store writes are less skewed because many hot-user events collapse
  into fewer windowed feature keys

The generated experiment log is:

```text
demo_data/week10/hotspot/results.jsonl
```
