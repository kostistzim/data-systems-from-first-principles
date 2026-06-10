from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


ALLOWED_EVENT_TYPES = {"click", "purchase", "view", "add_to_cart"}


@dataclass(frozen=True)
class QualityIssue:
    index: int
    field: str
    message: str
    value: object = None

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "field": self.field,
            "message": self.message,
            "value": self.value,
        }


@dataclass
class QualityReport:
    valid_events: list[dict]
    issues: list[QualityIssue]

    @property
    def valid_count(self) -> int:
        return len(self.valid_events)

    @property
    def invalid_count(self) -> int:
        invalid_indexes = {issue.index for issue in self.issues}
        return len(invalid_indexes)

    @property
    def total_count(self) -> int:
        return self.valid_count + self.invalid_count

    @property
    def ok(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict:
        return {
            "total_count": self.total_count,
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def validate_events(
    events: Iterable[Mapping[str, object]],
    require_timestamp: bool = False,
    allowed_event_types: Sequence[str] | None = None,
) -> QualityReport:
    allowed = set(allowed_event_types or ALLOWED_EVENT_TYPES)
    valid_events = []
    issues: list[QualityIssue] = []

    for index, event in enumerate(events):
        event_issues = validate_event(
            event,
            index=index,
            require_timestamp=require_timestamp,
            allowed_event_types=allowed,
        )
        if event_issues:
            issues.extend(event_issues)
        else:
            valid_events.append(dict(event))

    return QualityReport(valid_events=valid_events, issues=issues)


def validate_event(
    event: Mapping[str, object],
    index: int = 0,
    require_timestamp: bool = False,
    allowed_event_types: set[str] | None = None,
) -> list[QualityIssue]:
    allowed = allowed_event_types or ALLOWED_EVENT_TYPES
    issues: list[QualityIssue] = []

    user_id = event.get("user_id")
    if user_id is None or str(user_id).strip() == "":
        issues.append(QualityIssue(index, "user_id", "user_id is required", user_id))

    event_type = event.get("event_type")
    if event_type is None or str(event_type).strip() == "":
        issues.append(QualityIssue(index, "event_type", "event_type is required", event_type))
    else:
        normalized_type = str(event_type).strip().lower()
        if normalized_type not in allowed:
            issues.append(
                QualityIssue(
                    index,
                    "event_type",
                    f"event_type must be one of {sorted(allowed)}",
                    event_type,
                )
            )

    if require_timestamp:
        timestamp = event.get("timestamp")
        if timestamp is None:
            issues.append(QualityIssue(index, "timestamp", "timestamp is required", timestamp))
        elif not _is_number(timestamp):
            issues.append(QualityIssue(index, "timestamp", "timestamp must be numeric", timestamp))

    if "amount" in event and event.get("amount") is not None:
        amount = event.get("amount")
        if not _is_number(amount):
            issues.append(QualityIssue(index, "amount", "amount must be numeric", amount))
        elif float(amount) < 0:
            issues.append(QualityIssue(index, "amount", "amount must be non-negative", amount))

    return issues


def _is_number(value: object) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False
