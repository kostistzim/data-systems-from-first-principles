# MLStore-Lite: Week 9 Notes
## Online Feature Serving and Model Inference

## 1. Why Add An AI Layer

Weeks 1-8 built and evaluated the data infrastructure:

- storage engine
- replication
- sharding
- batch feature computation
- stream feature updates
- integration
- evaluation and observability

Week 9 adds a small AI/MLOps extension on top of that infrastructure.

The question changes from:

```text
Can we compute and store features?
```

to:

```text
Can a model use those stored features to produce predictions?
```

This is the natural end goal of a feature-store-style project. The feature store
is not useful only because it stores numbers. It is useful because models can
read those numbers at prediction time.

---

## 2. Architecture After Week 9

The full project architecture now looks like:

```text
Raw events
  -> Batch feature computation
  -> Stream feature updates
  -> Sharded replicated feature store
  -> Online feature server
  -> Model inference service
  -> Prediction log
```

This keeps the AI layer as a consumer of the previous layers.

The model does not replace the storage engine, replication, sharding, batch
processing, or stream processing. It depends on them.

That is the important systems idea:

```text
model inference quality depends on the data infrastructure behind it.
```

---

## 3. Online Feature Serving

Online feature serving means reading feature values at prediction time.

For example, a prediction request for user `42` needs values such as:

```text
feature:user:42:event_count
feature:user:42:click_count
feature:user:42:purchase_count
feature:user:42:total_purchase_amount
```

The stream layer may also have recent windowed features such as:

```text
feature:user:42:window:60:event_count
feature:user:42:window:60:click_count
```

The model should not know these storage key details. That is the job of the
feature server.

The `FeatureServer`:

- receives a user id
- builds the expected feature keys
- reads values from `MLStoreLiteSystem`
- converts values to numbers
- reports missing features
- summarizes recent stream-derived activity

So the feature server is the translation layer between:

```text
storage keys
```

and:

```text
model inputs
```

---

## 4. Model Inference

The implemented model is `PurchaseIntentModel`.

It is intentionally deterministic and dependency-free. There is no scikit-learn,
training job, neural network, or external model server.

The model estimates a purchase-intent probability from stored features:

```text
event_count
click_count
purchase_count
total_purchase_amount
recent_event_count
recent_click_count
recent_purchase_count
recent_total_purchase_amount
```

It uses a small weighted scoring function and a sigmoid transformation:

```text
probability = sigmoid(weighted feature score)
```

The model also performs serving-time checks:

- are expected batch features available?
- is there recent stream-derived activity?

If inputs are missing, the model lowers its confidence and records warnings.

Example output:

```json
{
  "user_id": "42",
  "model_version": "purchase-intent-v1",
  "purchase_probability": 0.73,
  "confidence": 0.82,
  "label": "likely_to_purchase",
  "warnings": []
}
```

This is more useful than a raw score because it separates:

- what the feature values suggest
- how much the serving layer trusts the available inputs

---

## 5. Inference Service

The `InferenceService` wires the AI layer together.

For one request:

```text
predict_user("42")
```

it does:

```text
FeatureServer -> PurchaseIntentModel -> PredictionLog
```

It also writes a structured log event using the Week 8 observability helpers.

This mirrors how real ML platforms separate responsibilities:

- feature serving retrieves inputs
- the model computes a prediction
- logging records what happened
- the service coordinates the request

---

## 6. Prediction Logging

The `PredictionLog` writes one JSON object per line.

The log includes:

- timestamp
- user id
- model version
- feature values
- prediction probability
- confidence
- label
- warnings

This matters for MLOps because predictions should be inspectable after they
happen.

If a prediction looks wrong, the log helps answer:

- what features did the model receive?
- were any features missing?
- which model version produced the prediction?
- what confidence did the system report?

---

## 7. What Was Implemented

Week 9 adds:

- `src/mlstore_lite/ai/feature_server.py`
- `src/mlstore_lite/ai/model.py`
- `src/mlstore_lite/ai/inference.py`
- `src/mlstore_lite/ai/prediction_log.py`
- `src/mlstore_lite/experiments/week9_ai_inference_demo.py`
- `tests/test_ai_inference.py`

It also updates:

- `docs/weekly-notes/README.md`
- the final report draft

---

## 8. Demo Flow

The Week 9 demo runs:

```text
batch events
  -> batch feature storage
stream events
  -> stream feature storage
user ids
  -> online feature serving
  -> model prediction
  -> prediction log
```

Run it with:

```text
python -m mlstore_lite.experiments.week9_ai_inference_demo
```

The generated prediction log is:

```text
demo_data/week9/ai/predictions.jsonl
```

---

## 9. Limitations

This is not a production ML serving system.

It does not include:

- model training
- a model registry
- an HTTP API
- deployment infrastructure
- online A/B testing
- drift monitoring
- external feature store services

The purpose is narrower:

```text
show how the existing feature pipeline can feed an online model inference layer.
```

That keeps the extension connected to the rest of MLStore-Lite.

---

## 10. How This Week Is Verified

The main verification commands are:

```text
python -m pytest -q
PYTHONPYCACHEPREFIX=/tmp/mlstore-pycache python -m compileall src tests
python -m mlstore_lite.experiments.week9_ai_inference_demo
```

The expected result is:

- all tests pass
- source files compile
- the Week 9 demo prints predictions
- `demo_data/week9/ai/predictions.jsonl` is created

The Week 9 extension completes the project as a miniature ML feature platform:

```text
events -> features -> feature store -> online inference -> prediction logs
```
