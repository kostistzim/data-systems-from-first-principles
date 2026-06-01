import time


class TimedResult:
    def __init__(self, label: str, elapsed_sec: float, result):
        self.label = label
        self.elapsed_sec = elapsed_sec
        self.result = result


def timed(label: str, fn) -> TimedResult:
    start = time.perf_counter()
    result = fn()
    elapsed_sec = time.perf_counter() - start
    return TimedResult(label=label, elapsed_sec=elapsed_sec, result=result)
