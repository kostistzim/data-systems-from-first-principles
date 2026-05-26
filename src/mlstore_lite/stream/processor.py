from typing import Optional, Union

from mlstore_lite.sharding import ShardedCluster

from .consumer import Consumer
from .windows import TumblingWindow


FeatureValue = Union[int, float]


class StreamFeatureProcessor:
    """
    Polls events, aggregates them by tumbling window, and writes features.
    """

    def __init__(
        self,
        consumer: Consumer,
        store: ShardedCluster,
        window: TumblingWindow,
    ):
        self.consumer = consumer
        self.store = store
        self.window = window

    def process_available(self, max_records: int = 100) -> dict:
        records = self.consumer.poll(max_records=max_records)
        if not records:
            return {}

        deltas = self._aggregate(records)
        outputs = self._apply_deltas(deltas)
        self.store.wait_for_all_replication()
        self.consumer.commit(records)
        return outputs

    def _aggregate(self, records: list[dict]) -> dict:
        deltas: dict[str, FeatureValue] = {}

        for record in records:
            event = record["event"]
            user_id = event.get("user_id")
            event_type = event.get("event_type")
            timestamp = event.get("timestamp")

            if user_id is None:
                raise ValueError("event is missing user_id")
            if event_type is None:
                raise ValueError("event is missing event_type")
            if timestamp is None:
                raise ValueError("event is missing timestamp")

            user = str(user_id)
            event_name = str(event_type)
            window_start = self.window.start_for(int(timestamp))

            add_delta(deltas, feature_key(user, window_start, "event_count"), 1)

            if event_name == "click":
                add_delta(deltas, feature_key(user, window_start, "click_count"), 1)
            elif event_name == "purchase":
                amount = float(event.get("amount", 0.0))
                add_delta(deltas, feature_key(user, window_start, "purchase_count"), 1)
                add_delta(
                    deltas,
                    feature_key(user, window_start, "total_purchase_amount"),
                    amount,
                )

        return deltas

    def _apply_deltas(self, deltas: dict) -> dict:
        outputs: dict[str, FeatureValue] = {}

        for key, delta in deltas.items():
            current = parse_feature_value(self.store.get(key))
            new_value = current + delta
            outputs[key] = normalize_feature_value(new_value)
            self.store.put(key, format_feature_value(outputs[key]))

        return outputs


def feature_key(user_id: str, window_start: int, feature_name: str) -> str:
    return f"feature:user:{user_id}:window:{window_start}:{feature_name}"


def add_delta(deltas: dict, key: str, value: FeatureValue) -> None:
    deltas[key] = deltas.get(key, 0) + value


def parse_feature_value(value: Optional[str]) -> FeatureValue:
    if value is None:
        return 0
    parsed = float(value)
    if parsed.is_integer():
        return int(parsed)
    return parsed


def normalize_feature_value(value: FeatureValue) -> FeatureValue:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def format_feature_value(value: FeatureValue) -> str:
    normalized = normalize_feature_value(value)
    return str(normalized)
