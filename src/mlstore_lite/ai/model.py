import math


class PurchaseIntentModel:
    """
    Small deterministic model for serving-time inference.

    It uses stored feature values to estimate purchase intent, then lowers
    confidence when expected serving-time inputs are unavailable.
    """

    def __init__(self, model_version: str = "purchase-intent-v1"):
        self.model_version = model_version
        self.weights = {
            "event_count": 0.05,
            "click_count": 0.08,
            "purchase_count": 0.75,
            "total_purchase_amount": 0.015,
            "recent_event_count": 0.06,
            "recent_click_count": 0.08,
            "recent_purchase_count": 0.9,
            "recent_total_purchase_amount": 0.02,
        }
        self.bias = -2.0

    def predict(self, served_features: dict) -> dict:
        features = served_features["features"]
        missing = served_features["missing"]
        checks = served_features["checks"]

        base_score = self.bias
        for name, weight in self.weights.items():
            base_score += weight * features.get(name, 0.0)

        base_probability = sigmoid(base_score)
        warnings = self._warnings(missing, checks)
        confidence = self._confidence(missing, checks)

        probability = clamp(base_probability * (0.75 + 0.25 * confidence), 0.0, 1.0)
        label = self._label(probability, confidence)

        return {
            "user_id": served_features["user_id"],
            "model_version": self.model_version,
            "purchase_probability": round(probability, 4),
            "base_probability": round(base_probability, 4),
            "confidence": round(confidence, 4),
            "label": label,
            "warnings": warnings,
            "features": features,
            "checks": checks,
        }

    def _warnings(self, missing: list[str], checks: dict) -> list[str]:
        warnings = [f"missing_{name}" for name in missing]
        if not checks["recent_activity_available"]:
            warnings.append("no_recent_stream_activity")
        return warnings

    def _confidence(self, missing: list[str], checks: dict) -> float:
        confidence = 1.0
        confidence -= 0.12 * len(missing)

        if checks["recent_windows_checked"] > 0 and not checks["recent_activity_available"]:
            confidence -= 0.2

        return clamp(confidence, 0.1, 1.0)

    def _label(self, probability: float, confidence: float) -> str:
        if confidence < 0.5:
            return "uncertain"
        if probability >= 0.7:
            return "likely_to_purchase"
        if probability >= 0.35:
            return "maybe_interested"
        return "low_intent"


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
