from typing import Iterable, Mapping, Union

from mlstore_lite.sharding import ShardedCluster

from .engine import BatchEngine, BatchRunResult


Event = Mapping[str, object]
FeatureValue = Union[int, float]


class FeatureBatchJob:
    def __init__(self, engine: BatchEngine):
        self.engine = engine

    def run(self, events: Iterable[Event]) -> BatchRunResult:
        return self.engine.run(events)

    def write_to_store(
        self,
        events: Iterable[Event],
        store: ShardedCluster,
    ) -> dict:
        result = self.run(events)

        for key, value in result.outputs.items():
            store.put(key, format_feature_value(value))

        store.wait_for_all_replication()
        return result.outputs


def make_user_feature_job(max_retries: int = 1) -> FeatureBatchJob:
    return FeatureBatchJob(
        engine=BatchEngine(
            mapper=map_user_event_to_features,
            reducer=sum_feature_values,
            max_retries=max_retries,
        )
    )


def map_user_event_to_features(event: Event) -> list[tuple[str, FeatureValue]]:
    user_id = event.get("user_id")
    event_type = event.get("event_type")

    if user_id is None:
        raise ValueError("event is missing user_id")
    if event_type is None:
        raise ValueError("event is missing event_type")

    user = str(user_id)
    event_name = str(event_type)
    pairs: list[tuple[str, FeatureValue]] = [
        (f"feature:user:{user}:event_count", 1)
    ]

    if event_name == "click":
        pairs.append((f"feature:user:{user}:click_count", 1))
    elif event_name == "purchase":
        amount = float(event.get("amount", 0.0))
        pairs.append((f"feature:user:{user}:purchase_count", 1))
        pairs.append((f"feature:user:{user}:total_purchase_amount", amount))

    return pairs


def sum_feature_values(key: str, values: list[FeatureValue]) -> FeatureValue:
    total = sum(values)
    if isinstance(total, float) and total.is_integer():
        return int(total)
    return total


def format_feature_value(value: FeatureValue) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)
