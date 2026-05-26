from .event_log import EventLog


class Producer:
    def __init__(self, event_log: EventLog):
        self.event_log = event_log

    def send(self, event: dict) -> int:
        return self.event_log.append(event)
