from mlstore_lite.quality import validate_events


def test_quality_validator_allows_valid_event():
    report = validate_events([
        {"user_id": "1", "event_type": "purchase", "amount": 10, "timestamp": 1}
    ], require_timestamp=True)

    assert report.ok
    assert report.valid_count == 1
    assert report.invalid_count == 0


def test_quality_validator_catches_missing_user_id():
    report = validate_events([
        {"event_type": "click", "timestamp": 1}
    ], require_timestamp=True)

    assert not report.ok
    assert report.invalid_count == 1
    assert report.issues[0].field == "user_id"


def test_quality_validator_catches_unknown_event_type_and_negative_amount():
    report = validate_events([
        {"user_id": "1", "event_type": "refund", "amount": -5}
    ])

    fields = {issue.field for issue in report.issues}

    assert report.invalid_count == 1
    assert "event_type" in fields
    assert "amount" in fields
