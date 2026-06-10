from dataclasses import dataclass, field
from typing import Iterable, Optional


@dataclass(frozen=True)
class FeatureMetadata:
    name: str
    key_pattern: str
    source: str
    value_type: str
    description: str
    used_by: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "key_pattern": self.key_pattern,
            "source": self.source,
            "value_type": self.value_type,
            "description": self.description,
            "used_by": list(self.used_by),
        }


class FeatureRegistry:
    """
    Small local catalog for feature meanings.

    The store keeps feature values as keys and strings. The registry explains
    what those keys mean and which layer creates them.
    """

    def __init__(self):
        self._features: dict[str, FeatureMetadata] = {}

    def register(self, metadata: FeatureMetadata) -> None:
        if metadata.name in self._features:
            raise ValueError(f"feature already registered: {metadata.name}")
        self._features[metadata.name] = metadata

    def get(self, name: str) -> Optional[FeatureMetadata]:
        return self._features.get(name)

    def require(self, name: str) -> FeatureMetadata:
        metadata = self.get(name)
        if metadata is None:
            raise KeyError(f"unknown feature: {name}")
        return metadata

    def list_features(self) -> list[FeatureMetadata]:
        return [self._features[name] for name in sorted(self._features)]

    def by_source(self, source: str) -> list[FeatureMetadata]:
        return [
            metadata
            for metadata in self.list_features()
            if metadata.source == source
        ]

    def to_dicts(self) -> list[dict]:
        return [metadata.to_dict() for metadata in self.list_features()]

    def __len__(self) -> int:
        return len(self._features)


def default_feature_registry() -> FeatureRegistry:
    registry = FeatureRegistry()
    for metadata in default_feature_metadata():
        registry.register(metadata)
    return registry


def default_feature_metadata() -> Iterable[FeatureMetadata]:
    model_users = ("purchase-intent-v1", "tiny-attention-recommender-v1")
    return [
        FeatureMetadata(
            name="event_count",
            key_pattern="feature:user:{user_id}:event_count",
            source="batch",
            value_type="number",
            description="Total number of historical events observed for a user.",
            used_by=model_users,
        ),
        FeatureMetadata(
            name="click_count",
            key_pattern="feature:user:{user_id}:click_count",
            source="batch",
            value_type="number",
            description="Number of historical click-like events observed for a user.",
            used_by=model_users,
        ),
        FeatureMetadata(
            name="purchase_count",
            key_pattern="feature:user:{user_id}:purchase_count",
            source="batch",
            value_type="number",
            description="Number of historical purchase events observed for a user.",
            used_by=model_users,
        ),
        FeatureMetadata(
            name="total_purchase_amount",
            key_pattern="feature:user:{user_id}:total_purchase_amount",
            source="batch",
            value_type="number",
            description="Total purchase amount observed for a user.",
            used_by=model_users,
        ),
        FeatureMetadata(
            name="recent_event_count",
            key_pattern="feature:user:{user_id}:window:{window_start}:event_count",
            source="stream",
            value_type="number",
            description="Number of recent events for a user inside a stream window.",
            used_by=("purchase-intent-v1",),
        ),
        FeatureMetadata(
            name="recent_click_count",
            key_pattern="feature:user:{user_id}:window:{window_start}:click_count",
            source="stream",
            value_type="number",
            description="Number of recent click-like events inside a stream window.",
            used_by=("purchase-intent-v1",),
        ),
        FeatureMetadata(
            name="recent_purchase_count",
            key_pattern="feature:user:{user_id}:window:{window_start}:purchase_count",
            source="stream",
            value_type="number",
            description="Number of recent purchases inside a stream window.",
            used_by=("purchase-intent-v1",),
        ),
        FeatureMetadata(
            name="recent_total_purchase_amount",
            key_pattern="feature:user:{user_id}:window:{window_start}:total_purchase_amount",
            source="stream",
            value_type="number",
            description="Recent purchase amount inside a stream window.",
            used_by=("purchase-intent-v1",),
        ),
        FeatureMetadata(
            name="purchase_probability",
            key_pattern="prediction:user:{user_id}:purchase_probability",
            source="model",
            value_type="number",
            description="Purchase probability produced by an inference model.",
            used_by=("reporting", "lineage"),
        ),
        FeatureMetadata(
            name="prediction_label",
            key_pattern="prediction:user:{user_id}:label",
            source="model",
            value_type="string",
            description="Readable prediction label produced by an inference model.",
            used_by=("reporting", "lineage"),
        ),
    ]
