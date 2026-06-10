# Final Demo

The final demo is the quickest way to see the full MLStore-Lite pipeline in one
run.

It executes:

```text
batch events
  -> batch feature computation
stream events
  -> stream feature updates
features
  -> sharded replicated store
stored features
  -> online feature serving
  -> purchase-intent predictions
  -> prediction log
```

## Terminal Demo

Run:

```bash
make demo
```

This is the recommended grading/submission path because it has no optional UI
dependency.

The underlying Python command is:

```bash
python -m mlstore_lite.experiments.final_demo
```

## What To Inspect

After running the demo, look for:

- batch feature counts
- stream feature counts
- consumer offset
- shard distribution
- prediction probabilities
- prediction warnings for missing or incomplete feature context

These outputs are intentionally small. The goal is to make the architecture
visible, not to benchmark performance.

## Related Reading Material In The Repo

- `docs/architecture.md`: final system overview
- `docs/runbook.md`: all local and Docker commands
- `docs/weekly-notes/`: week-by-week learning notes
- `docs/final-report-draft/final-report.md`: report draft
- `docs/final-report-draft/results.md`: representative local results

## Generated Output

The demo writes generated files under:

```text
demo_data/final_demo/
```

These files are useful for inspection but should not be committed.
