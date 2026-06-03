from typing import Optional


BATCH_FEATURES = (
    "event_count",
    "click_count",
    "purchase_count",
    "total_purchase_amount",
)

WINDOW_FEATURES = (
    "event_count",
    "click_count",
    "purchase_count",
    "total_purchase_amount",
)


class FeatureServer:
    """
    Reads model features from MLStore-Lite.

    The model should not need to know storage key conventions. This class keeps
    that translation in one place.
    """

    def __init__(
        self,
        system,
        recent_window_starts: Optional[list[int]] = None,
    ):
        self.system = system
        self.recent_window_starts = recent_window_starts or []

    def get_user_features(self, user_id: str) -> dict:
        user = str(user_id)
        features = {}
        missing = []
        source_keys = {}

        for feature_name in BATCH_FEATURES:
            key = batch_feature_key(user, feature_name)
            value = self._read_number(key)
            source_keys[feature_name] = key

            if value is None:
                features[feature_name] = 0.0
                missing.append(feature_name)
            else:
                features[feature_name] = value

        recent_feature_totals = {
            f"recent_{feature_name}": 0.0 for feature_name in WINDOW_FEATURES
        }
        windows_with_activity = 0

        for window_start in self.recent_window_starts:
            event_count_key = window_feature_key(user, window_start, "event_count")
            event_count = self._read_number(event_count_key)
            if event_count is not None and event_count > 0:
                windows_with_activity += 1

            for feature_name in WINDOW_FEATURES:
                key = window_feature_key(user, window_start, feature_name)
                value = self._read_number(key)
                if value is not None:
                    recent_feature_totals[f"recent_{feature_name}"] += value

        features.update(recent_feature_totals)

        checks = {
            "batch_features_available": len(missing) == 0,
            "recent_activity_available": windows_with_activity > 0,
            "recent_windows_checked": len(self.recent_window_starts),
            "recent_windows_with_activity": windows_with_activity,
        }

        return {
            "user_id": user,
            "features": features,
            "missing": missing,
            "checks": checks,
            "source_keys": source_keys,
        }

    def _read_number(self, key: str) -> Optional[float]:
        raw_value = self.system.get_feature(key)
        if raw_value is None:
            return None
        return float(raw_value)


def batch_feature_key(user_id: str, feature_name: str) -> str:
    return f"feature:user:{user_id}:{feature_name}"


def window_feature_key(user_id: str, window_start: int, feature_name: str) -> str:
    return f"feature:user:{user_id}:window:{window_start}:{feature_name}"
