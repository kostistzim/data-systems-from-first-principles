import json

from mlstore_lite.lineage import LineageLog


def test_lineage_log_writes_json_lines_record(tmp_path):
    path = tmp_path / "lineage.jsonl"
    log = LineageLog(str(path))

    record = log.record_prediction(
        user_id="42",
        model_version="purchase-intent-v1",
        input_feature_keys=["feature:user:42:click_count"],
        output_keys=["prediction:user:42:purchase_probability"],
        missing_features=[],
    )

    records = log.read_all()
    raw_line = path.read_text().strip()

    assert record["record_type"] == "prediction_lineage"
    assert records[0]["user_id"] == "42"
    assert json.loads(raw_line)["model_version"] == "purchase-intent-v1"
