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
python -m mlstore_lite.experiments.final_demo
```

This is the recommended grading/submission path because it has no optional UI
dependency.

## Optional Streamlit Project Viewer

Install the optional UI dependency:

```bash
python -m pip install ".[ui]"
```

Run:

```bash
streamlit run src/mlstore_lite/experiments/final_demo_app.py
```

The UI reuses the same `run_final_demo()` function as the terminal command. It
does not implement a separate pipeline.

The UI is meant to feel like a small project walkthrough rather than only a
dashboard. It uses sidebar navigation and clickable next-step buttons. It
includes:

- a guided home page
- a visual end-to-end flow chart
- a layer-by-layer architecture guide
- a DDIA learning map that connects chapters to implementation milestones
- representative results
- final report draft
- weekly notes, selected one at a time
- limitations and future-work pages

## Generated Output

The demo writes generated files under:

```text
demo_data/final_demo/
```

These files are useful for inspection but should not be committed.
