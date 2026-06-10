from mlstore_lite.training import UserEvent, Vocabulary, event_to_tokens

from .sequential_model import TinyAttentionRecommender


class SequentialInferenceService:
    """
    Converts recent user events into model tokens and returns a prediction.
    """

    def __init__(self, model: TinyAttentionRecommender, vocabulary: Vocabulary):
        self.model = model
        self.vocabulary = vocabulary

    def predict_from_events(self, user_id: str, events: list[UserEvent]) -> dict:
        ordered_events = sorted(events, key=lambda item: item.timestamp)
        tokens = []
        for event in ordered_events:
            tokens.extend(event_to_tokens(event))
        return self.model.predict_tokens(user_id, tokens, self.vocabulary)
