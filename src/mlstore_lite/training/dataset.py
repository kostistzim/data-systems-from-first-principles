import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class UserEvent:
    user_id: str
    event_type: str
    item_id: str
    timestamp: int


def load_retailrocket_events(
    path: str,
    max_rows: Optional[int] = None,
) -> list[UserEvent]:
    """
    Load events from the RetailRocket Kaggle dataset.

    Expected columns are: timestamp, visitorid, event, itemid.
    The returned shape is the internal event shape used by Week 11.
    """
    events: list[UserEvent] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_number, row in enumerate(reader, start=1):
            if max_rows is not None and row_number > max_rows:
                break

            events.append(
                UserEvent(
                    user_id=str(row["visitorid"]),
                    event_type=normalize_event_type(row["event"]),
                    item_id=str(row["itemid"]),
                    timestamp=int(float(row["timestamp"])),
                )
            )
    return events


def normalize_event_type(event_type: str) -> str:
    value = event_type.strip().lower()
    if value == "addtocart":
        return "add_to_cart"
    if value == "transaction":
        return "purchase"
    return value


def sample_retail_events() -> list[UserEvent]:
    """
    Small built-in sample so the Week 11 demo runs without downloading Kaggle.

    The patterns are intentionally simple: some users view only, some add to
    cart, and some purchase after repeated interest. The real dataset can be
    dropped into data/raw/retailrocket/events.csv later.
    """
    rows = [
        ("0", "view", "laptop", 1),
        ("0", "view", "laptop", 2),
        ("0", "add_to_cart", "laptop", 3),
        ("0", "view", "mouse", 4),
        ("0", "purchase", "laptop", 5),
        ("1", "view", "phone", 1),
        ("1", "view", "case", 2),
        ("1", "add_to_cart", "phone", 3),
        ("1", "purchase", "phone", 6),
        ("2", "view", "keyboard", 1),
        ("2", "view", "monitor", 2),
        ("2", "view", "monitor", 3),
        ("3", "view", "camera", 1),
        ("3", "add_to_cart", "camera", 2),
        ("3", "view", "lens", 3),
        ("3", "purchase", "camera", 4),
        ("4", "view", "book", 1),
        ("4", "view", "book", 2),
        ("4", "view", "pen", 3),
        ("5", "view", "tablet", 1),
        ("5", "add_to_cart", "tablet", 2),
        ("5", "view", "tablet", 3),
        ("5", "purchase", "tablet", 5),
        ("6", "view", "chair", 1),
        ("6", "view", "desk", 2),
        ("7", "view", "headphones", 1),
        ("7", "add_to_cart", "headphones", 3),
        ("8", "view", "speaker", 1),
        ("8", "view", "speaker", 2),
        ("8", "add_to_cart", "speaker", 4),
        ("8", "purchase", "speaker", 6),
    ]
    return [
        UserEvent(user_id=user_id, event_type=event_type, item_id=item_id, timestamp=ts)
        for user_id, event_type, item_id, ts in rows
    ]


def load_events_or_sample(
    path: str = "data/raw/retailrocket/events.csv",
    max_rows: Optional[int] = None,
) -> tuple[list[UserEvent], str]:
    if Path(path).exists():
        return load_retailrocket_events(path, max_rows=max_rows), path
    return sample_retail_events(), "built-in sample"


def to_batch_events(events: Iterable[UserEvent]) -> list[dict]:
    batch_events = []
    for event in events:
        event_type = "purchase" if event.event_type == "purchase" else "click"
        amount = 1.0 if event.event_type == "purchase" else 0.0
        payload = {"user_id": event.user_id, "event_type": event_type}
        if amount:
            payload["amount"] = amount
        batch_events.append(payload)
    return batch_events
