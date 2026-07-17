import os
import sys
import subprocess
import json
import pytest


PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

TEST_TARGET = os.environ.get("TEST_TARGET", "v3")

CRITICAL_MODULES = {
    "app.py": 30,
    "main.py": 30,
    "verifier.py": 30,
    "validator.py": 30,
}

COVERAGE_SOURCE = "api/MVPv3"

COVERAGE_JSON = os.path.join(PROJECT_ROOT, "coverage.json")


def cleanup():
    for name in (".coverage", "coverage.json", ".coverage.lock"):
        p = os.path.join(PROJECT_ROOT, name)
        if os.path.exists(p):
            os.remove(p)


class TestQRT003CriticalModuleCoverage:

    def test_critical_modules_have_sufficient_coverage(self):
        cleanup()

        run_result = subprocess.run(
            [sys.executable, "-m", "coverage", "run",
             f"--source={COVERAGE_SOURCE}",
             "-m", "pytest", "tests/",
             "--ignore=tests/test_qrt_003_critical_module_coverage.py",
             "--ignore=tests/test_qrt_005_docs_availability.py",
             "--ignore=tests/test_qrt_006_solver_optimality.py",
             "-q", "--tb=short"],
            capture_output=True, text=True,
            cwd=PROJECT_ROOT, timeout=600,
        )

        assert run_result.returncode == 0, (
            f"Test suite exited with code {run_result.returncode}:\n"
            f"{run_result.stdout}\n{run_result.stderr}"
        )

        json_result = subprocess.run(
            [sys.executable, "-m", "coverage", "json"],
            capture_output=True, text=True,
            cwd=PROJECT_ROOT, timeout=30,
        )

        assert json_result.returncode == 0, (
            f"coverage json failed:\n{json_result.stderr}"
        )

        if not os.path.exists(COVERAGE_JSON):
            pytest.fail(f"Coverage JSON not found at {COVERAGE_JSON}")

        with open(COVERAGE_JSON) as f:
            coverage_data = json.load(f)

        failures = []
        actual = {}
        for module, threshold in CRITICAL_MODULES.items():
            pct = self._get_module_coverage(coverage_data, module)
            actual[module] = pct
            if pct is None:
                failures.append(
                    f"{module}: NOT FOUND (threshold: {threshold}%)"
                )
            elif pct < threshold:
                failures.append(
                    f"{module}: {pct:.1f}% (threshold: {threshold}%)"
                )

        cleanup()

        if failures:
            lines = [f"Critical modules below coverage threshold (>=30%) for {COVERAGE_SOURCE}:"]
            for m, p in actual.items():
                status = "OK" if (p is not None and p >= 30) else "FAIL"
                p_str = f"{p:.1f}%" if p is not None else "N/A"
                lines.append(f"  {m:20s} {p_str:>8s}  {status}")
            lines.append("")
            for f in failures:
                lines.append(f"  {f}")
            pytest.fail("\n".join(lines))

    @staticmethod
    def _get_module_coverage(coverage_data, module_name):
        result = None
        for file_path, file_data in coverage_data.get("files", {}).items():
            if file_path.replace("\\", "/").endswith(module_name):
                raw = file_data.get("summary", {}).get("percent_covered_display")
                if raw is not None:
                    pct = float(raw)
                    if result is None or pct > result:
                        result = pct
        return result
