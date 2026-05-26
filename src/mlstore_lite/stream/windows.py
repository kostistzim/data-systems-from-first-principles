class TumblingWindow:
    """
    Fixed-size, non-overlapping event-time windows.
    """

    def __init__(self, size_seconds: int):
        if size_seconds <= 0:
            raise ValueError("size_seconds must be > 0")
        self.size_seconds = size_seconds

    def start_for(self, timestamp: int) -> int:
        if timestamp < 0:
            raise ValueError("timestamp must be >= 0")
        return (timestamp // self.size_seconds) * self.size_seconds

    def end_for(self, timestamp: int) -> int:
        return self.start_for(timestamp) + self.size_seconds
