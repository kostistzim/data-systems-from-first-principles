# Sequential Recommender Extension

The final AI extension adds a small sequence-based recommender. The previous
inference layer used feature counts from the feature store. This extension also
uses event order.

The prediction question is:

```text
Given this user's recent sequence of events, do they look likely to purchase?
```

A count-based model can see that a user had three views and one add-to-cart. A
sequence model can also see whether the add-to-cart happened recently, and what
came before it.

## Architecture

```text
raw events
  -> user histories
  -> token vocabulary
  -> tiny attention recommender
  -> purchase probability
  -> prediction log
  -> sharded store prediction keys
```

The model is intentionally small. It uses the main ideas behind Transformer-style
sequence models, but without adding a heavy deep-learning framework:

- events and items become tokens
- tokens become numeric IDs
- IDs become embeddings
- position information is added
- attention weighs the recent sequence
- a scoring head estimates purchase probability

This keeps the implementation understandable while still moving beyond simple
feature counting.

## Dataset

The code can read the RetailRocket ecommerce dataset if the CSV is placed at:

```text
data/raw/retailrocket/events.csv
```

The dataset itself is not committed to the repository. If the file is missing,
the demo uses a small built-in sample so that the project remains easy to run.

## Relation To DDIA

This layer connects back to the systems work from earlier weeks:

| Earlier layer | Role in the recommender story |
|---|---|
| Storage | stores prediction keys and generated feature values |
| Replication | keeps several copies of each shard |
| Sharding | routes prediction and feature keys by hash |
| Batch | computes historical user features |
| Stream | gives a natural source of ordered user events |
| Observability | logs training metrics and prediction records |

The AI layer is therefore not a separate notebook. It is the final consumer of
the data infrastructure.

## Limitations

This is not a full production recommender system. It does not use GPUs, PyTorch,
large embeddings, negative sampling, candidate retrieval, or online model
serving. The point is to show the architecture in a small form.

A future version could replace this educational model with a real Transformer,
a two-tower retrieval model, or a Mamba-style state-space model for longer event
histories.
