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
PYTHONPATH=src python3 src/mlstore_lite/experiments/week8_evaluation.py
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
PYTHONPATH=src python3 src/mlstore_lite/experiments/week9_ai_inference_demo.py
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
