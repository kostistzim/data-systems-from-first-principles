import pytest

from mlstore_lite.catalog import FeatureMetadata, FeatureRegistry, default_feature_registry


def test_default_feature_registry_contains_core_features():
    registry = default_feature_registry()

    click_count = registry.require("click_count")

    assert click_count.source == "batch"
    assert "purchase-intent-v1" in click_count.used_by
    assert len(registry) >= 8


def test_feature_registry_rejects_duplicate_names():
    registry = FeatureRegistry()
    metadata = FeatureMetadata(
        name="x",
        key_pattern="feature:x",
        source="test",
        value_type="number",
        description="test feature",
    )

    registry.register(metadata)

    with pytest.raises(ValueError):
        registry.register(metadata)


def test_feature_registry_filters_by_source():
    registry = default_feature_registry()

    stream_features = registry.by_source("stream")

    assert stream_features
    assert all(feature.source == "stream" for feature in stream_features)
