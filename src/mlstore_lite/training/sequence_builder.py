from dataclasses import dataclass
from typing import Iterable

from .dataset import UserEvent


@dataclass(frozen=True)
class SequenceExample:
    user_id: str
    input_tokens: list[str]
    label: int
    target_event_type: str
    target_item_id: str
    timestamp: int


def event_to_tokens(event: UserEvent) -> list[str]:
    return [f"event:{event.event_type}", f"item:{event.item_id}"]


def build_user_histories(events: Iterable[UserEvent]) -> dict[str, list[UserEvent]]:
    histories: dict[str, list[UserEvent]] = {}
    for event in events:
        histories.setdefault(event.user_id, []).append(event)

    for user_events in histories.values():
        user_events.sort(key=lambda item: item.timestamp)

    return histories


def build_sequence_examples(
    events: Iterable[UserEvent],
    max_history_events: int = 10,
    positive_event_type: str = "purchase",
) -> list[SequenceExample]:
    """
    Build training rows from ordered user histories.

    Each example asks: given the previous events for this user, is the next
    event a purchase? This keeps the model close to an online recommender.
    """
    examples: list[SequenceExample] = []
    histories = build_user_histories(events)

    for user_id, user_events in histories.items():
        for index in range(1, len(user_events)):
            history = user_events[max(0, index - max_history_events) : index]
            target = user_events[index]
            tokens = flatten_event_tokens(history)
            if not tokens:
                continue

            examples.append(
                SequenceExample(
                    user_id=user_id,
                    input_tokens=tokens,
                    label=1 if target.event_type == positive_event_type else 0,
                    target_event_type=target.event_type,
                    target_item_id=target.item_id,
                    timestamp=target.timestamp,
                )
            )

    return examples


def flatten_event_tokens(events: Iterable[UserEvent]) -> list[str]:
    tokens: list[str] = []
    for event in events:
        tokens.extend(event_to_tokens(event))
    return tokens
