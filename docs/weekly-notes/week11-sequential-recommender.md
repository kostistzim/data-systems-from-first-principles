# Week 11: Sequential Recommender

Week 11 adds a more realistic AI layer on top of MLStore-Lite.

The earlier AI layer used stored feature counts such as:

```text
click_count = 8
purchase_count = 3
recent_event_count = 5
```

That is useful, but it ignores order. A sequence model looks at the order of a
user's actions:

```text
view laptop -> view laptop -> add_to_cart laptop -> purchase laptop
```

This is closer to how recommender systems think about behavior. The question is
not only "how many things happened?" but also "what happened recently, and in
what order?"

## What Was Added

New training utilities:

```text
src/mlstore_lite/training/
```

This folder turns raw events into ordered user histories and training examples.
It can read a RetailRocket-style Kaggle CSV if it exists at:

```text
data/raw/retailrocket/events.csv
```

If the file is not there, the demo uses a small built-in sample. That keeps the
repo runnable without committing a large dataset.

New AI code:

```text
src/mlstore_lite/ai/sequential_model.py
src/mlstore_lite/ai/sequential_inference.py
src/mlstore_lite/ai/audit.py
```

New runnable scripts:

```text
python -m mlstore_lite.experiments.week11_train_sequential_recommender
python -m mlstore_lite.experiments.week11_recommender_demo
```

## The Model Idea

The model is a small Transformer-style recommender. It is not a huge neural
network. It is a small educational version of the same idea.

It has:

- token IDs
- embeddings
- a position signal
- attention over recent user history
- a scoring head that returns purchase probability

A user history is converted into tokens:

```text
event:view
item:laptop
event:add_to_cart
item:laptop
```

The vocabulary maps those tokens to numbers. The model then attends over the
sequence and estimates whether the user looks likely to purchase.

## Why This Fits The Project

This layer consumes the system built in the previous weeks.

```text
events
  -> batch and stream features
  -> sharded replicated store
  -> sequential recommender
  -> prediction log
```

The model does not replace the data-system work. It gives that work a final
consumer.

The storage layer stores prediction outputs. The sharding layer routes
prediction keys. The observability layer records training metrics and prediction
logs. The event pipeline provides the raw material for user histories.

## What Gets Saved

Training creates local generated files:

```text
model_artifacts/week11/tiny_attention_recommender.json
model_artifacts/week11/vocabulary.json
demo_data/week11/training_metrics.json
demo_data/week11/experiments.jsonl
```

The recommender demo writes:

```text
demo_data/week11/recommender_demo/predictions.jsonl
```

These files are generated output, not source code.

## How To Read The Results

The demo prints predictions like:

```text
user=0 probability=0.6123 confidence=0.8341 label=maybe_interested
```

It also prints the tokens with the highest attention. This is useful because it
shows which parts of the recent history mattered most to the model.

The result should not be treated as a production recommender benchmark. The goal
is to show the architecture:

```text
ordered behavior -> sequence model -> prediction -> logged output
```

## Future Work

A stronger version could replace the tiny attention model with:

- a PyTorch Transformer recommender
- a two-tower retrieval model
- a graph recommender
- a Mamba/state-space sequence model for longer user histories

For this project, the small attention model is enough to make the AI layer more
interesting while keeping the repo readable.
