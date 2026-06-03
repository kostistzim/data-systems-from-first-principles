from mlstore_lite.ai import (
    FeatureServer,
    InferenceService,
    PredictionLog,
    PurchaseIntentModel,
)
from mlstore_lite.integration import create_mlstore_lite_system


def test_feature_server_returns_numeric_features_for_existing_user(tmp_path):
    system = create_mlstore_lite_system(str(tmp_path))
    system.run_batch_features(
        [
            {"user_id": "42", "event_type": "click"},
            {"user_id": "42", "event_type": "purchase", "amount": 15.0},
        ]
    )
    system.produce_event({"user_id": "42", "event_type": "click", "timestamp": 5})
    system.process_stream_events(max_records=10)

    server = FeatureServer(system, recent_window_starts=[0])
    served = server.get_user_features("42")

    assert served["features"]["event_count"] == 2.0
    assert served["features"]["click_count"] == 1.0
    assert served["features"]["purchase_count"] == 1.0
    assert served["features"]["total_purchase_amount"] == 15.0
    assert served["features"]["recent_event_count"] == 1.0
    assert served["missing"] == []
    assert served["checks"]["recent_activity_available"] is True


def test_feature_server_reports_missing_features_for_unknown_user(tmp_path):
    system = create_mlstore_lite_system(str(tmp_path))
    server = FeatureServer(system, recent_window_starts=[0])

    served = server.get_user_features("missing")

    assert served["features"]["event_count"] == 0.0
    assert served["missing"] == [
        "event_count",
        "click_count",
        "purchase_count",
        "total_purchase_amount",
    ]
    assert served["checks"]["recent_activity_available"] is False


def test_purchase_intent_model_lowers_confidence_when_inputs_are_missing():
    model = PurchaseIntentModel()
    complete = {
        "user_id": "1",
        "features": {
            "event_count": 10.0,
            "click_count": 8.0,
            "purchase_count": 2.0,
            "total_purchase_amount": 30.0,
            "recent_event_count": 2.0,
            "recent_click_count": 2.0,
            "recent_purchase_count": 0.0,
            "recent_total_purchase_amount": 0.0,
        },
        "missing": [],
        "checks": {
            "batch_features_available": True,
            "recent_activity_available": True,
            "recent_windows_checked": 1,
            "recent_windows_with_activity": 1,
        },
    }
    incomplete = {
        **complete,
        "missing": ["event_count", "click_count"],
        "checks": {
            "batch_features_available": False,
            "recent_activity_available": False,
            "recent_windows_checked": 1,
            "recent_windows_with_activity": 0,
        },
    }

    complete_prediction = model.predict(complete)
    incomplete_prediction = model.predict(incomplete)

    assert incomplete_prediction["confidence"] < complete_prediction["confidence"]
    assert "missing_event_count" in incomplete_prediction["warnings"]
    assert "no_recent_stream_activity" in incomplete_prediction["warnings"]


def test_inference_service_records_prediction(tmp_path):
    system = create_mlstore_lite_system(str(tmp_path / "system"))
    system.run_batch_features(
        [
            {"user_id": "7", "event_type": "click"},
            {"user_id": "7", "event_type": "purchase", "amount": 10.0},
        ]
    )

    prediction_log = PredictionLog(str(tmp_path / "predictions.jsonl"))
    service = InferenceService(
        feature_server=FeatureServer(system, recent_window_starts=[]),
        model=PurchaseIntentModel(),
        prediction_log=prediction_log,
    )

    prediction = service.predict_user("7")
    records = prediction_log.read_all()

    assert prediction["user_id"] == "7"
    assert 0.0 <= prediction["purchase_probability"] <= 1.0
    assert 0.0 <= prediction["confidence"] <= 1.0
    assert prediction["label"] in {
        "likely_to_purchase",
        "maybe_interested",
        "low_intent",
        "uncertain",
    }
    assert len(records) == 1
    assert records[0]["user_id"] == "7"
    assert records[0]["model_version"] == "purchase-intent-v1"
