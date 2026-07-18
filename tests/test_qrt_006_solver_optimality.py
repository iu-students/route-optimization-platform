import json
import os
import sys
import glob
import pytest

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

for p in [
    os.path.join(PROJECT_ROOT, "api", "MVPv3"),
    os.path.join(PROJECT_ROOT, "api", "MVPv3", "CP-SAT"),
    os.path.join(PROJECT_ROOT, "api", "MVPv3", "Shared"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)

from tester import calc_cost, load_json

BASELINE_PATH = os.path.join(PROJECT_ROOT, "instances", "baseline_scores.json")
INSTANCES_DIR = os.path.join(PROJECT_ROOT, "instances")

PASS_THRESHOLD = 7


@pytest.fixture(scope="session")
def baseline_scores():
    with open(BASELINE_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def instance_paths():
    paths = sorted(glob.glob(os.path.join(INSTANCES_DIR, "i[0-9]*.json")))
    return [p for p in paths if os.path.basename(p).startswith("i") and os.path.basename(p).endswith(".json")]


def run_solver(instance_path, tmp_path):
    import importlib.util

    base = os.path.join(PROJECT_ROOT, "api", "MVPv2.2")
    if not os.path.exists(base):
        base = os.path.join(PROJECT_ROOT, "api", "MVPv2")

    main_path = os.path.join(base, "CP-SAT", "main.py")
    if not os.path.exists(main_path):
        pytest.skip("solver pipeline not available")

    for p in [os.path.join(base, "Shared"),
              os.path.join(base, "Web"),
              os.path.join(base, "CP-SAT"),
              base]:
        if p not in sys.path:
            sys.path.insert(0, p)

    spec = importlib.util.spec_from_file_location("qrt006_solver", main_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    output_path = os.path.join(tmp_path, f"output_{os.path.basename(instance_path)}")
    solution = mod.solve_pipeline(input_path=instance_path, output_path=output_path)

    # Use tester.calc_cost for consistent cost calculation with baseline
    input_data = load_json(instance_path)
    analyzed = calc_cost(input_data, solution)
    total_cost = analyzed['cost']['total']

    return total_cost


class TestQRTSolverOptimality:

    def test_all_instances_have_baseline(self, baseline_scores, instance_paths):
        missing = []
        for p in instance_paths:
            key = "baseline_" + os.path.basename(p).replace(".json", "")
            if key not in baseline_scores:
                missing.append(key)
        assert not missing, f"missing baseline entries for: {missing}"

    def test_solver_beats_baseline_on_at_least_7_of_10(self, baseline_scores, instance_paths, tmp_path):
        results = {}
        beats = 0
        total = len(instance_paths)

        for p in instance_paths:
            key = "baseline_" + os.path.basename(p).replace(".json", "")
            score = run_solver(p, tmp_path)
            baseline = baseline_scores.get(key, float("inf"))
            is_beat = score < baseline
            results[key] = {
                "solver_score": round(score, 2),
                "baseline": round(baseline, 2),
                "beat": is_beat,
            }
            if is_beat:
                beats += 1

        print(f"\n--- QRT-006 results: {beats}/{total} instances beat baseline ---")
        for k, v in sorted(results.items()):
            status = "BEAT" if v["beat"] else "MISS"
            print(f"  {k}: solver={v['solver_score']} baseline={v['baseline']} [{status}]")

        assert beats >= PASS_THRESHOLD, (
            f"solver beat baseline on {beats}/{total} instances "
            f"(threshold: {PASS_THRESHOLD}/{total})"
        )
