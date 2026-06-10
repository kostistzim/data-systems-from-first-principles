import argparse
import os
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Step:
    name: str
    command: list[str]
    env: dict[str, str] | None = None


def main() -> None:
    args = parse_args()
    steps = build_steps(quick=args.quick, skip_tests=args.skip_tests)

    print("=== MLSTORE-LITE RUNNER ===", flush=True)
    print(f"mode={'quick' if args.quick else 'full'}", flush=True)
    print(f"steps={len(steps)}", flush=True)
    print("", flush=True)

    for index, step in enumerate(steps, start=1):
        run_step(index, len(steps), step)

    print("\nAll selected steps completed successfully.", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run MLStore-Lite verification and demo commands.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a shorter reviewer-friendly path: tests, final demo, and Week 11 demo.",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Run demos only. Useful when tests already ran in CI or locally.",
    )
    return parser.parse_args()


def build_steps(quick: bool, skip_tests: bool) -> list[Step]:
    python = sys.executable
    steps: list[Step] = []

    if not skip_tests:
        steps.append(Step("unit and integration tests", [python, "-m", "pytest", "-q"]))

    if quick:
        steps.extend(
            [
                Step("final end-to-end demo", [python, "-m", "mlstore_lite.experiments.final_demo"]),
                Step("Week 11 recommender demo", [python, "-m", "mlstore_lite.experiments.week11_recommender_demo"]),
            ]
        )
        return steps

    steps.extend(
        [
            Step(
                "compile check",
                [python, "-m", "compileall", "src", "tests"],
                env={"PYTHONPYCACHEPREFIX": "/tmp/mlstore-pycache"},
            ),
            Step("Week 8 evaluation", [python, "-m", "mlstore_lite.experiments.week8_evaluation"]),
            Step("Week 9 AI inference demo", [python, "-m", "mlstore_lite.experiments.week9_ai_inference_demo"]),
            Step("Week 10 scaling experiment", [python, "-m", "mlstore_lite.experiments.week10_scaling_experiment"]),
            Step("Week 10 hotspot experiment", [python, "-m", "mlstore_lite.experiments.week10_hotspot_experiment"]),
            Step("Week 11 recommender training", [python, "-m", "mlstore_lite.experiments.week11_train_sequential_recommender"]),
            Step("Week 11 recommender demo", [python, "-m", "mlstore_lite.experiments.week11_recommender_demo"]),
            Step("Week 12 metadata lineage quality demo", [python, "-m", "mlstore_lite.experiments.week12_metadata_lineage_quality_demo"]),
            Step("final end-to-end demo", [python, "-m", "mlstore_lite.experiments.final_demo"]),
        ]
    )
    return steps


def run_step(index: int, total: int, step: Step) -> None:
    print(f"[{index}/{total}] {step.name}", flush=True)
    print("$ " + " ".join(step.command), flush=True)

    env = os.environ.copy()
    if step.env:
        env.update(step.env)

    subprocess.run(step.command, check=True, env=env)
    print("", flush=True)


if __name__ == "__main__":
    main()
