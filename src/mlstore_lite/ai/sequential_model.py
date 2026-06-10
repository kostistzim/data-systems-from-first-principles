import hashlib
import json
import math
import os
from dataclasses import dataclass
from typing import Optional

from mlstore_lite.training import SequenceExample, Vocabulary


@dataclass
class SequencePrediction:
    user_id: str
    purchase_probability: float
    label: str
    confidence: float
    sequence_length: int
    important_tokens: list[dict]
    model_version: str

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "purchase_probability": round(self.purchase_probability, 4),
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "sequence_length": self.sequence_length,
            "important_tokens": self.important_tokens,
            "model_version": self.model_version,
        }


class TinyAttentionRecommender:
    """
    Small Transformer-style sequential recommender.

    This is not a production neural network. It is an educational model with the
    same main ideas in miniature: token IDs, embeddings, position signal,
    attention over the recent sequence, and a scoring head.
    """

    def __init__(
        self,
        max_sequence_length: int = 20,
        embedding_dim: int = 16,
        model_version: str = "tiny-attention-recommender-v1",
    ):
        self.max_sequence_length = max_sequence_length
        self.embedding_dim = embedding_dim
        self.model_version = model_version
        self.weight_vector = [0.0 for _ in range(embedding_dim)]
        self.bias = 0.0
        self.positive_rate = 0.0
        self.token_scores: dict[str, float] = {}
        self.trained = False

    def fit(self, examples: list[SequenceExample], vocabulary: Vocabulary) -> dict:
        if not examples:
            raise ValueError("TinyAttentionRecommender requires at least one example")

        positive_contexts = []
        negative_contexts = []
        labels = []
        token_label_totals: dict[str, int] = {}
        token_counts: dict[str, int] = {}

        for example in examples:
            encoded = vocabulary.encode_fixed(
                example.input_tokens,
                length=self.max_sequence_length,
            )
            context, _ = self._attention_context(encoded, vocabulary)
            labels.append(example.label)
            if example.label == 1:
                positive_contexts.append(context)
            else:
                negative_contexts.append(context)

            for token in set(example.input_tokens):
                token_label_totals[token] = token_label_totals.get(token, 0) + example.label
                token_counts[token] = token_counts.get(token, 0) + 1

        self.positive_rate = sum(labels) / len(labels)
        self.token_scores = {
            token: token_label_totals[token] / token_counts[token]
            for token in token_counts
        }
        positive_center = _mean_vector(positive_contexts, self.embedding_dim)
        negative_center = _mean_vector(negative_contexts, self.embedding_dim)
        self.weight_vector = [
            0.75 * (positive_center[i] - negative_center[i])
            for i in range(self.embedding_dim)
        ]
        self.bias = _safe_logit(self.positive_rate)
        self.trained = True

        return self.evaluate(examples, vocabulary)

    def predict_tokens(
        self,
        user_id: str,
        input_tokens: list[str],
        vocabulary: Vocabulary,
    ) -> dict:
        if not self.trained:
            raise ValueError("model must be fitted or loaded before prediction")

        encoded = vocabulary.encode_fixed(input_tokens, length=self.max_sequence_length)
        context, attention = self._attention_context(encoded, vocabulary)
        score = self.bias + _dot(context, self.weight_vector)
        score += self._token_attention_signal(attention)
        score += self._recent_behavior_signal(input_tokens)
        probability = _sigmoid(score)
        known_tokens = [token for token in input_tokens if token in vocabulary.token_to_id]
        known_ratio = len(known_tokens) / max(1, len(input_tokens))
        confidence = _clamp(0.45 + abs(probability - 0.5) + 0.25 * known_ratio, 0.1, 1.0)

        prediction = SequencePrediction(
            user_id=user_id,
            purchase_probability=probability,
            label=self._label(probability, confidence),
            confidence=confidence,
            sequence_length=len(input_tokens),
            important_tokens=attention[:5],
            model_version=self.model_version,
        )
        return prediction.to_dict()

    def evaluate(self, examples: list[SequenceExample], vocabulary: Vocabulary) -> dict:
        predictions = [
            self.predict_tokens(example.user_id, example.input_tokens, vocabulary)
            for example in examples
        ]
        predicted_labels = [1 if item["purchase_probability"] >= 0.5 else 0 for item in predictions]
        gold_labels = [example.label for example in examples]
        return binary_metrics(gold_labels, predicted_labels)

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {
            "max_sequence_length": self.max_sequence_length,
            "embedding_dim": self.embedding_dim,
            "model_version": self.model_version,
            "weight_vector": self.weight_vector,
            "token_scores": self.token_scores,
            "bias": self.bias,
            "positive_rate": self.positive_rate,
            "trained": self.trained,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

    @classmethod
    def load(cls, path: str) -> "TinyAttentionRecommender":
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        model = cls(
            max_sequence_length=int(payload["max_sequence_length"]),
            embedding_dim=int(payload["embedding_dim"]),
            model_version=str(payload["model_version"]),
        )
        model.weight_vector = [float(value) for value in payload["weight_vector"]]
        model.token_scores = {
            str(token): float(score)
            for token, score in payload.get("token_scores", {}).items()
        }
        model.bias = float(payload["bias"])
        model.positive_rate = float(payload["positive_rate"])
        model.trained = bool(payload["trained"])
        return model

    def _attention_context(
        self,
        encoded_tokens: list[int],
        vocabulary: Vocabulary,
    ) -> tuple[list[float], list[dict]]:
        non_pad = [
            (position, token_id)
            for position, token_id in enumerate(encoded_tokens)
            if token_id != vocabulary.pad_id
        ]
        if not non_pad:
            return [0.0 for _ in range(self.embedding_dim)], []

        query_position, query_token_id = non_pad[-1]
        query = self._embedding(query_token_id, query_position)
        raw_scores = []
        values = []

        for position, token_id in non_pad:
            key = self._embedding(token_id, position)
            value = self._embedding(token_id, position)
            recency_bonus = 0.03 * position
            raw_scores.append((_dot(query, key) / math.sqrt(self.embedding_dim)) + recency_bonus)
            values.append((position, token_id, value))

        weights = _softmax(raw_scores)
        context = [0.0 for _ in range(self.embedding_dim)]
        attention_rows = []

        for weight, (position, token_id, value) in zip(weights, values):
            for dim in range(self.embedding_dim):
                context[dim] += weight * value[dim]
            attention_rows.append(
                {
                    "token": vocabulary.token_for_id(token_id),
                    "position": position,
                    "attention": round(weight, 4),
                }
            )

        attention_rows.sort(key=lambda item: item["attention"], reverse=True)
        return context, attention_rows

    def _embedding(self, token_id: int, position: int) -> list[float]:
        values = []
        for dim in range(self.embedding_dim):
            digest = hashlib.sha256(f"{token_id}:{dim}".encode("utf-8")).hexdigest()
            base = (int(digest[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
            position_signal = math.sin((position + 1) / (10000 ** (dim / self.embedding_dim)))
            values.append(0.85 * base + 0.15 * position_signal)
        return values

    def _token_attention_signal(self, attention: list[dict]) -> float:
        signal = 0.0
        for row in attention:
            token = row["token"]
            token_score = self.token_scores.get(token, self.positive_rate)
            signal += row["attention"] * (token_score - self.positive_rate)
        return 6.0 * signal

    def _recent_behavior_signal(self, input_tokens: list[str]) -> float:
        recent_tokens = input_tokens[-8:]
        signal = 0.0
        if "event:add_to_cart" in recent_tokens:
            signal += 0.9
        if "event:purchase" in recent_tokens:
            signal += 1.2
        if recent_tokens.count("event:view") >= 3:
            signal += 0.25
        return signal

    def _label(self, probability: float, confidence: float) -> str:
        if confidence < 0.45:
            return "uncertain"
        if probability >= 0.65:
            return "likely_to_purchase"
        if probability >= 0.4:
            return "maybe_interested"
        return "low_intent"


def binary_metrics(gold_labels: list[int], predicted_labels: list[int]) -> dict:
    true_positive = sum(1 for y, p in zip(gold_labels, predicted_labels) if y == 1 and p == 1)
    true_negative = sum(1 for y, p in zip(gold_labels, predicted_labels) if y == 0 and p == 0)
    false_positive = sum(1 for y, p in zip(gold_labels, predicted_labels) if y == 0 and p == 1)
    false_negative = sum(1 for y, p in zip(gold_labels, predicted_labels) if y == 1 and p == 0)

    accuracy = (true_positive + true_negative) / max(1, len(gold_labels))
    precision = true_positive / max(1, true_positive + false_positive)
    recall = true_positive / max(1, true_positive + false_negative)
    f1 = 2 * precision * recall / max(0.000001, precision + recall)

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "confusion_matrix": {
            "true_positive": true_positive,
            "true_negative": true_negative,
            "false_positive": false_positive,
            "false_negative": false_negative,
        },
    }


def train_test_split(
    examples: list[SequenceExample],
    test_ratio: float = 0.3,
) -> tuple[list[SequenceExample], list[SequenceExample]]:
    if len(examples) < 3:
        return examples, examples
    split_index = max(1, int(len(examples) * (1.0 - test_ratio)))
    return examples[:split_index], examples[split_index:]


def _mean_vector(vectors: list[list[float]], dim: int) -> list[float]:
    if not vectors:
        return [0.0 for _ in range(dim)]
    return [sum(vector[index] for vector in vectors) / len(vectors) for index in range(dim)]


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _softmax(values: list[float]) -> list[float]:
    max_value = max(values)
    exps = [math.exp(value - max_value) for value in values]
    total = sum(exps)
    return [value / total for value in exps]


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def _safe_logit(probability: float) -> float:
    clipped = _clamp(probability, 0.01, 0.99)
    return math.log(clipped / (1.0 - clipped))


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
