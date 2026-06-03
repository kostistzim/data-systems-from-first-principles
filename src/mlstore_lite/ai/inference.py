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
        logger=None,
    ):
        self.feature_server = feature_server
        self.model = model
        self.prediction_log = prediction_log
        self.logger = logger or get_logger("mlstore_lite.ai")

    def predict_user(self, user_id: str) -> dict:
        served_features = self.feature_server.get_user_features(user_id)
        prediction = self.model.predict(served_features)
        self.prediction_log.record(prediction)

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
