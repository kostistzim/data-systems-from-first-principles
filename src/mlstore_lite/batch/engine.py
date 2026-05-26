from collections import defaultdict
from typing import Any, Callable, DefaultDict, Iterable, List, Optional, Tuple


Mapper = Callable[[Any], Iterable[Tuple[Any, Any]]]
Reducer = Callable[[Any, List[Any]], Any]


class BatchRunResult:
    def __init__(
        self,
        mapped_pairs: List[Tuple[Any, Any]],
        grouped_values: dict[Any, List[Any]],
        outputs: dict[Any, Any],
    ):
        self.mapped_pairs = mapped_pairs
        self.grouped_values = grouped_values
        self.outputs = outputs


class BatchEngine:
    """
    Small local Map -> Shuffle -> Reduce engine.

    It is intentionally local and simple, but it keeps the same conceptual
    stages as larger batch systems: produce intermediate records, group by key,
    then reduce each group into one result.
    """

    def __init__(
        self,
        mapper: Mapper,
        reducer: Reducer,
        max_retries: int = 1,
    ):
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")

        self.mapper = mapper
        self.reducer = reducer
        self.max_retries = max_retries

    def run(
        self,
        records: Iterable[Any],
    ) -> BatchRunResult:
        mapped_pairs: List[Tuple[Any, Any]] = []

        for record in records:
            pairs = self._run_with_retry(lambda: list(self.mapper(record)), "map")
            mapped_pairs.extend(pairs)

        grouped_values = shuffle_pairs(mapped_pairs)
        outputs: dict[Any, Any] = {}

        for key, values in grouped_values.items():
            outputs[key] = self._run_with_retry(
                lambda key=key, values=values: self.reducer(key, values),
                "reduce",
            )

        return BatchRunResult(
            mapped_pairs=mapped_pairs,
            grouped_values=dict(grouped_values),
            outputs=outputs,
        )

    def _run_with_retry(self, fn: Callable[[], Any], stage: str) -> Any:
        attempts = self.max_retries + 1
        last_error: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            try:
                return fn()
            except Exception as exc:
                last_error = exc
                if attempt == attempts:
                    break

        raise RuntimeError(
            f"Batch {stage} stage failed after {attempts} attempt(s)"
        ) from last_error


def shuffle_pairs(mapped_pairs: Iterable[Tuple[Any, Any]]) -> dict[Any, List[Any]]:
    grouped: DefaultDict[Any, List[Any]] = defaultdict(list)
    for key, value in mapped_pairs:
        grouped[key].append(value)
    return dict(grouped)
