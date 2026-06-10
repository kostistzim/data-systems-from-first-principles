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
  -> sequential recommender extension
  -> metadata, lineage, and data quality
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

Show the available project commands:

```bash
make help
```

Run the quick reviewer path:

```bash
make quick
```

This runs tests, the final terminal demo, and the Week 11 recommender demo.

Run the full local verification path:

```bash
make all
```

Run the full test suite:

```bash
make test
```

Optionally run the compile check on macOS/Linux:

```bash
make compile
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run the Week 8 evaluation script:

```bash
make week8
```

Run the Week 9 AI inference demo:

```bash
make week9
```

Run the Week 10 scaling experiments:

```bash
make week10
```

Run the final terminal demo:

```bash
make demo
```

Run the Week 11 sequential recommender:

```bash
make week11
```

Run the Week 12 inspection layer:

```bash
make week12
```

Docker is optional, but useful for checking the project in a clean environment:

```bash
make docker-build
make docker-run
```

For reviewing the project, start with:

- `docs/architecture.md` for the final system shape
- `docs/runbook.md` for all run commands
- `docs/final-demo.md` for the terminal demo
- `docs/weekly-notes/` for the learning diary
- `docs/final-report-draft/` for report material

The old development commands used `PYTHONPATH=src`, but installing the project
with `python -m pip install -r requirements.txt` makes that unnecessary.

## Repo Map

- `src/mlstore_lite/`: implementation code
- `tests/`: unit and integration tests
- `docs/architecture.md`: compact architecture overview
- `docs/runbook.md`: practical run commands
- `docs/cloud-architecture.md`: possible cloud version of the architecture
- `docs/weekly-notes/`: learning notes for Weeks 1-12
- `docs/final-report-draft/`: report draft and supporting material

Generated demo output goes under `demo_data/`. It is useful for inspection, but
it is not core source code.

Large raw datasets should go under `data/raw/`, and generated model artifacts
should go under `model_artifacts/`. Both are ignored by git.

## Learning Context

This project is also a learning artifact. With a math background and less than
two years of coding experience, the purpose was to go deeper into software
architecture and data-system design rather than only use high-level ML tools.
Future iterations may revisit the project with the second edition of DDIA and
add small implementations inspired by *System Design Interview*.
