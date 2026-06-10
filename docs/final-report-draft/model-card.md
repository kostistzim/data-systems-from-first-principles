# Model Card: Tiny Attention Recommender

## Model

`tiny-attention-recommender-v1`

## Purpose

Predict whether a user looks likely to purchase based on their recent ordered
event history.

## Inputs

The model receives a sequence of tokens such as:

```text
event:view, item:laptop, event:add_to_cart, item:laptop
```

## Output

The model returns:

- purchase probability
- label
- confidence
- most important recent tokens

## Intended Use

This model is used as an educational final AI layer for MLStore-Lite. It shows
how a feature/event infrastructure can support model inference and prediction
logging.

## Not Intended For

It should not be used for real ecommerce decisions. It is trained on a tiny
sample unless the user manually adds a larger dataset.

## Main Limitations

- small local model
- no production training pipeline
- no hyperparameter tuning
- no fairness analysis
- no online serving API
- no real-time model updates

## Why It Is Useful Here

It makes the final project more realistic because many ML systems care about
ordered behavior, not only feature counts. It also gives the storage, sharding,
streaming, and observability layers a concrete AI consumer.
