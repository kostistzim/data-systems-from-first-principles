# MLStore-Lite

MLStore-Lite is a small educational data-systems project for understanding how
machine-learning-style feature infrastructure can be built from simpler pieces.
It is inspired by selected chapters of *Designing Data-Intensive Applications*,
but it stays local, dependency-light, and readable on purpose.

The goal is not to compete with production tools. The goal is to make their
architecture easier to reason about by implementing small versions of the core
ideas.

## Architecture

The final project follows this flow:

```text
storage
  -> replication
  -> sharding
  -> batch processing
  -> stream processing
  -> integration
  -> observability
  -> online feature serving and inference
  -> local scaling experiments
```

In practical terms:

```text
events -> features -> sharded replicated feature store -> model prediction logs
```

The current local topology uses:

- 2 shards
- replication factor 3 per shard
- local node directories instead of real networked machines

## Quickstart

Run the full test suite:

```bash
/opt/anaconda3/bin/python3 -m pytest -q
```

Run the compile check:

```bash
PYTHONPYCACHEPREFIX=/tmp/mlstore-pycache python3 -m compileall src tests
```

Run the Week 8 evaluation script:

```bash
PYTHONPATH=src python3 src/mlstore_lite/experiments/week8_evaluation.py
```

Run the Week 9 AI inference demo:

```bash
PYTHONPATH=src python3 src/mlstore_lite/experiments/week9_ai_inference_demo.py
```

Run the Week 10 scaling experiments:

```bash
PYTHONPATH=src python3 src/mlstore_lite/experiments/week10_scaling_experiment.py
PYTHONPATH=src python3 src/mlstore_lite/experiments/week10_hotspot_experiment.py
```

`PYTHONPATH=src` tells Python to import the local package from `src/mlstore_lite`.

## Repo Map

- `src/mlstore_lite/`: implementation code
- `tests/`: unit and integration tests
- `docs/architecture.md`: compact architecture overview
- `docs/cloud-architecture.md`: possible cloud version of the architecture
- `docs/weekly-notes/`: learning notes for Weeks 1-10
- `docs/final-report-draft/`: report draft and supporting material

Generated demo output goes under `demo_data/`. It is useful for inspection, but
it is not core source code.

## Learning Context

This project is also a learning artifact. With a math background and less than
two years of coding experience, the purpose was to go deeper into software
architecture and data-system design rather than only use high-level ML tools.
Future iterations may revisit the project with the second edition of DDIA and
add small implementations inspired by *System Design Interview*.
