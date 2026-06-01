import json

from mlstore_lite.observability import ExperimentLog, get_logger, timed
from mlstore_lite.observability.logging import log_event


def test_experiment_log_writes_json_lines_records(tmp_path):
    path = tmp_path / "results.jsonl"
    log = ExperimentLog(str(path))

    record = log.record(
        experiment="batch_runtime",
        metric="elapsed_time",
        value=0.12,
        unit="seconds",
        parameters={"events": 10},
    )

    with open(path, "r", encoding="utf-8") as f:
        line = f.readline()

    loaded = json.loads(line)
    assert loaded["experiment"] == "batch_runtime"
    assert loaded["metric"] == "elapsed_time"
    assert loaded["value"] == 0.12
    assert loaded["unit"] == "seconds"
    assert loaded["parameters"] == {"events": 10}
    assert record == loaded
    assert log.read_all() == [loaded]


def test_timed_returns_elapsed_time_and_result():
    result = timed("simple_sum", lambda: sum([1, 2, 3]))

    assert result.label == "simple_sum"
    assert result.result == 6
    assert result.elapsed_sec >= 0


def test_structured_logger_can_log_event(capsys):
    logger = get_logger("mlstore_lite.test_observability")

    log_event(logger, "test_event", component="observability")

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["message"] == "test_event"
    assert payload["component"] == "observability"
