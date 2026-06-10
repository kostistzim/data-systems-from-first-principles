from mlstore_lite.ai import SequentialInferenceService, TinyAttentionRecommender
from mlstore_lite.ai.audit import summarize_predictions
from mlstore_lite.training import (
    Vocabulary,
    build_sequence_examples,
    build_user_histories,
    sample_retail_events,
)


def test_sequence_builder_orders_user_histories():
    histories = build_user_histories(sample_retail_events())

    timestamps = [event.timestamp for event in histories["0"]]

    assert timestamps == sorted(timestamps)


def test_vocabulary_encodes_and_pads_sequences():
    vocabulary = Vocabulary.build([["event:view", "item:laptop"]])

    encoded = vocabulary.encode_fixed(["event:view"], length=3)

    assert encoded[0] == vocabulary.pad_id
    assert encoded[1] == vocabulary.pad_id
    assert encoded[2] == vocabulary.token_to_id["event:view"]


def test_tiny_attention_recommender_trains_and_predicts():
    examples = build_sequence_examples(sample_retail_events())
    vocabulary = Vocabulary.build([example.input_tokens for example in examples])
    model = TinyAttentionRecommender(max_sequence_length=12, embedding_dim=8)

    metrics = model.fit(examples, vocabulary)
    prediction = model.predict_tokens("0", examples[0].input_tokens, vocabulary)

    assert "accuracy" in metrics
    assert 0.0 <= prediction["purchase_probability"] <= 1.0
    assert prediction["important_tokens"]


def test_sequential_inference_service_uses_recent_events():
    events = sample_retail_events()
    examples = build_sequence_examples(events)
    vocabulary = Vocabulary.build([example.input_tokens for example in examples])
    model = TinyAttentionRecommender(max_sequence_length=12, embedding_dim=8)
    model.fit(examples, vocabulary)
    service = SequentialInferenceService(model, vocabulary)

    prediction = service.predict_from_events("0", [event for event in events if event.user_id == "0"])

    assert prediction["user_id"] == "0"
    assert prediction["sequence_length"] > 0


def test_prediction_audit_summarizes_outputs():
    predictions = [
        {"purchase_probability": 0.8, "confidence": 0.9, "label": "likely_to_purchase"},
        {"purchase_probability": 0.2, "confidence": 0.7, "label": "low_intent"},
    ]

    summary = summarize_predictions(predictions)

    assert summary["prediction_count"] == 2
    assert summary["labels"]["likely_to_purchase"] == 1
