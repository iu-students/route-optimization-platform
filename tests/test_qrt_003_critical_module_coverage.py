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
COVERAGE_FILE = os.path.join(PROJECT_ROOT, ".coverage")

_COV_ENSURED = False


def _cleanup_artifacts():
    for name in ("coverage.json", ".coverage.lock"):
        p = os.path.join(PROJECT_ROOT, name)
        if os.path.exists(p):
            os.remove(p)


def _ensure_coverage_file():
    global _COV_ENSURED
    if _COV_ENSURED:
        return True
    if os.path.exists(COVERAGE_FILE):
        _COV_ENSURED = True
        return True
    try:
        import coverage
        cov = coverage.Coverage.current()
        if cov is not None:
            cov.save()
            _COV_ENSURED = True
            return True
    except Exception:
        pass
    return False


CRITICAL_TEST_FILES = [
    "tests/test_main.py",
    "tests/test_verifier.py",
    "tests/test_validator.py",
    "tests/test_tester.py",
    "tests/test_integration_cpsat.py",
    "tests/test_qrt_001_api_responsiveness.py",
    "tests/test_qrt_002_api_confidentiality.py",
]


class TestQRT003CriticalModuleCoverage:

    def test_critical_modules_have_sufficient_coverage(self):
        _cleanup_artifacts()

        if not _ensure_coverage_file():
            run_result = subprocess.run(
                [sys.executable, "-m", "coverage", "run",
                 f"--source={COVERAGE_SOURCE}",
                 "-m", "pytest"] + CRITICAL_TEST_FILES +
                ["-q", "--tb=short"],
                capture_output=True, text=True,
                cwd=PROJECT_ROOT, timeout=600,
            )
            assert run_result.returncode == 0, (
                f"Coverage run exited with code {run_result.returncode}:\n"
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

        _cleanup_artifacts()

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
