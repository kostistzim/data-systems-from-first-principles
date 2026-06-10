# Runbook

This page is the practical "how do I run it?" guide for MLStore-Lite.

The project can be run in three ways:

1. direct Python commands
2. Makefile commands
3. Docker

For reviewing the project, the Makefile is the easiest path.

## Recommended Local Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project:

```bash
python -m pip install -r requirements.txt
```

The package configuration lives in `pyproject.toml`. The `requirements.txt`
file is only a small convenience wrapper.

## Main Commands

Show all Makefile commands:

```bash
make help
```

Run tests:

```bash
make test
```

Run the final terminal demo:

```bash
make demo
```

Run the quick reviewer path:

```bash
make quick
```

This runs:

```text
tests -> final demo -> Week 11 recommender demo
```

Run the full local verification path:

```bash
make all
```

This runs:

```text
tests
compile check
Week 8 evaluation
Week 9 inference demo
Week 10 scaling experiment
Week 10 hotspot experiment
Week 11 recommender training
Week 11 recommender demo
final demo
```

## Week-Specific Commands

```bash
make week8
make week9
make week10
make week11
```

These are useful when reading the weekly notes and wanting to run only the code
for that part of the project.

## Direct Python Runner

The Makefile calls this script internally:

```bash
python -m mlstore_lite.experiments.run_all --quick
python -m mlstore_lite.experiments.run_all
```

If the project has not been installed, use:

```bash
PYTHONPATH=src python -m mlstore_lite.experiments.run_all --quick
```

## Docker

Docker is optional. It is included to make the project easier to run on another
machine with a clean Python environment.

Build the image:

```bash
make docker-build
```

Run the container:

```bash
make docker-run
```

Equivalent direct Docker commands:

```bash
docker build -t mlstore-lite .
docker run --rm mlstore-lite
```

The Docker container runs the quick path by default:

```text
tests -> final demo -> Week 11 recommender demo
```

## Generated Output

The demos write local generated files under:

```text
demo_data/
model_artifacts/
```

These are ignored by git. They are useful for inspection, but they are not core
source code.

Large downloaded datasets should go under:

```text
data/raw/
```

That folder is also ignored by git.
