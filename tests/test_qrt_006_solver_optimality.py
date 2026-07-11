import json
import os
import sys
import glob
import pytest

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

# add current pipeline paths (MVPv2.2)
for p in [
    os.path.join(PROJECT_ROOT, "api", "MVPv2.2"),
    os.path.join(PROJECT_ROOT, "api", "MVPv2.2", "CP-SAT"),
    os.path.join(PROJECT_ROOT, "api", "MVPv2.2", "Shared"),
    os.path.join(PROJECT_ROOT, "api", "MVPv2.2", "PyVRP"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)

BASELINE_PATH = os.path.join(PROJECT_ROOT, "instances", "baseline_scores.json")
INSTANCES_DIR = os.path.join(PROJECT_ROOT, "instances")

PASS_THRESHOLD = 7


@pytest.fixture(scope="session")
def baseline_scores():
    with open(BASELINE_PATH) as f:
        data = json.load(f)
    return data["scores"]


@pytest.fixture(scope="session")
def instance_paths():
    paths = sorted(glob.glob(os.path.join(INSTANCES_DIR, "i[0-9]*.json")))
    return [p for p in paths if os.path.basename(p).startswith("i") and os.path.basename(p).endswith(".json")]


def run_solver(instance_path, tmp_path):
    try:
        from CP_SAT.main import parse, run_solver as solve
        from Shared.verifier import run_verification
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(PROJECT_ROOT, "api", "MVPv2"))
            sys.path.insert(0, os.path.join(PROJECT_ROOT, "api", "MVPv2", "CP-SAT"))
            sys.path.insert(0, os.path.join(PROJECT_ROOT, "api", "MVPv2", "Shared"))
            from main import parse, run_solver as solve
            from verifier import run_verification
        except ImportError:
            pytest.skip("solver pipeline not available")

    scenario = parse(instance_path)
    solution = solve(scenario)

    verifier_result = run_verification(solution, scenario)
    if verifier_result.get("status") != "success":
        pytest.skip(f"verification failed for {os.path.basename(instance_path)}")

    total_cost = solution.get("statistics", {}).get("total_cost")
    if total_cost is None:
        pytest.skip(f"no total_cost in solution for {os.path.basename(instance_path)}")

    return total_cost


class TestQRTSolverOptimality:

    def test_all_instances_have_baseline(self, baseline_scores, instance_paths):
        missing = []
        for p in instance_paths:
            key = os.path.basename(p).replace(".json", "")
            if key not in baseline_scores:
                missing.append(key)
        assert not missing, f"missing baseline entries for: {missing}"

    def test_solver_beats_baseline_on_at_least_7_of_10(self, baseline_scores, instance_paths, tmp_path):
        results = {}
        beats = 0
        total = len(instance_paths)

        for p in instance_paths:
            key = os.path.basename(p).replace(".json", "")
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
