from mlstore_lite.integration import create_mlstore_lite_system


def test_integrated_system_runs_batch_and_stream_features(tmp_path):
    system = create_mlstore_lite_system(str(tmp_path / "system"))

    batch_outputs = system.run_batch_features(
        [
            {"user_id": "42", "event_type": "click"},
            {"user_id": "42", "event_type": "purchase", "amount": 10.0},
        ]
    )
    system.produce_events(
        [
            {"user_id": "42", "event_type": "click", "timestamp": 10},
            {"user_id": "42", "event_type": "click", "timestamp": 20},
        ]
    )
    stream_outputs = system.process_stream_events(max_records=10)

    assert batch_outputs["feature:user:42:event_count"] == 2
    assert stream_outputs["feature:user:42:window:0:click_count"] == 2
    assert system.get_feature("feature:user:42:event_count") == "2"
    assert system.get_feature("feature:user:42:window:0:click_count") == "2"
    assert system.consumer.current_offset() == 2


def test_integrated_system_continues_after_manual_failover(tmp_path):
    system = create_mlstore_lite_system(str(tmp_path / "system"))

    new_leader = system.failover_shard("shard-a")
    system.produce_event(
        {"user_id": "7", "event_type": "purchase", "amount": 4.0, "timestamp": 70}
    )
    outputs = system.process_stream_events(max_records=10)

    assert new_leader != "shard-a-leader"
    assert outputs["feature:user:7:window:60:purchase_count"] == 1
    assert system.get_feature("feature:user:7:window:60:total_purchase_amount") == "4"


def test_integrated_system_status_reports_all_layers(tmp_path):
    system = create_mlstore_lite_system(str(tmp_path / "system"))
    system.run_batch_features([{"user_id": "1", "event_type": "click"}])

    status = system.status()

    assert status["consumer_offset"] == 0
    assert sum(status["key_distribution"].values()) > 0
    assert len(status["shards"]) == 2
    assert all(len(shard["replicas"]) == 3 for shard in status["shards"])
