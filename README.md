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

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project:

```bash
python -m pip install -r requirements.txt
```

Packaging is defined in `pyproject.toml`. The `requirements.txt` file is only a
small convenience wrapper for installing the project with its development
dependency, `pytest`.

Run the full test suite:

```bash
python -m pytest -q
```

Optionally run the compile check on macOS/Linux:

```bash
PYTHONPYCACHEPREFIX=/tmp/mlstore-pycache python -m compileall src tests
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run the Week 8 evaluation script:

```bash
python -m mlstore_lite.experiments.week8_evaluation
```

Run the Week 9 AI inference demo:

```bash
python -m mlstore_lite.experiments.week9_ai_inference_demo
```

Run the Week 10 scaling experiments:

```bash
python -m mlstore_lite.experiments.week10_scaling_experiment
python -m mlstore_lite.experiments.week10_hotspot_experiment
```

Run the final terminal demo:

```bash
python -m mlstore_lite.experiments.final_demo
```

For reviewing the project, start with:

- `docs/architecture.md` for the final system shape
- `docs/final-demo.md` for the terminal demo
- `docs/weekly-notes/` for the learning diary
- `docs/final-report-draft/` for report material

The old development commands used `PYTHONPATH=src`, but installing the project
with `python -m pip install -r requirements.txt` makes that unnecessary.

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
