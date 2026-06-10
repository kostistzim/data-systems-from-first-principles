from mlstore_lite.observability import get_logger, log_event


class InferenceService:
    """
    Coordinates online feature serving, model inference, and prediction logging.
    """

    def __init__(
        self,
        feature_server,
        model,
        prediction_log,
        lineage_log=None,
        logger=None,
    ):
        self.feature_server = feature_server
        self.model = model
        self.prediction_log = prediction_log
        self.lineage_log = lineage_log
        self.logger = logger or get_logger("mlstore_lite.ai")

    def predict_user(self, user_id: str) -> dict:
        served_features = self.feature_server.get_user_features(user_id)
        prediction = self.model.predict(served_features)
        self.prediction_log.record(prediction)
        self._record_lineage(served_features, prediction)

        log_event(
            self.logger,
            "prediction_recorded",
            user_id=prediction["user_id"],
            model_version=prediction["model_version"],
            label=prediction["label"],
            purchase_probability=prediction["purchase_probability"],
            confidence=prediction["confidence"],
            warnings=prediction["warnings"],
        )

        return prediction

    def _record_lineage(self, served_features: dict, prediction: dict) -> None:
        if self.lineage_log is None:
            return

        source_keys = list(served_features.get("source_keys", {}).values())
        source_keys.extend(served_features.get("recent_source_keys", []))
        user_id = prediction["user_id"]
        output_keys = [
            f"prediction:user:{user_id}:purchase_probability",
            f"prediction:user:{user_id}:label",
        ]

        self.lineage_log.record_prediction(
            user_id=user_id,
            model_version=prediction["model_version"],
            input_feature_keys=source_keys,
            output_keys=output_keys,
            missing_features=served_features.get("missing", []),
            extra={
                "label": prediction["label"],
                "confidence": prediction["confidence"],
            },
        )
