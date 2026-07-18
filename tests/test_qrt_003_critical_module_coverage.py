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


CRITICAL_TEST_FILES = [
    "tests/test_main.py",
    "tests/test_verifier.py",
    "tests/test_validator.py",
    "tests/test_tester.py",
    "tests/test_integration_cpsat.py",
    "tests/test_qrt_001_api_responsiveness.py",
    "tests/test_qrt_002_api_confidentiality.py",
]


def _cleanup_artifacts():
    for name in ("coverage.json", ".coverage.lock"):
        p = os.path.join(PROJECT_ROOT, name)
        if os.path.exists(p):
            os.remove(p)


_RELOAD_MODULES = [
    "app",
    "Web.validator",
    "Shared.models",
    "Shared.verifier",
    "Shared.history",
    "CP-SAT.main",
    "main",
    "vehicle_routes",
    "loader_routes",
]


def _run_critical_tests_under_coverage():
    try:
        import coverage as _cmod
        import pytest as _ptmod
        import importlib as _il
    except ImportError:
        return False
    try:
        cov = _cmod.Coverage(source=[COVERAGE_SOURCE])
        cov.start()
        for _m in _RELOAD_MODULES:
            if _m in sys.modules:
                try:
                    _il.reload(sys.modules[_m])
                except Exception:
                    pass
        exit_code = _ptmod.main(
            CRITICAL_TEST_FILES + ["-q", "--tb=short", "--no-header", "-p", "no:cacheprovider"],
            plugins=[],
        )
        cov.stop()
        cov.save()
        return exit_code == 0
    except Exception:
        return False


def _has_critical_module_data():
    try:
        import coverage as _c
        c = _c.Coverage()
        c.load()
        data = c.get_data()
        for fpath in data.measured_files():
            norm = fpath.replace("\\", "/")
            if any(norm.endswith(m) for m in CRITICAL_MODULES):
                return True
    except Exception:
        pass
    return False


def _ensure_coverage_file():
    global _COV_ENSURED
    if _COV_ENSURED:
        return True
    if os.path.exists(COVERAGE_FILE) and _has_critical_module_data():
        _COV_ENSURED = True
        return True
    try:
        import coverage
        cov = coverage.Coverage.current()
        if cov is not None:
            cov.save()
            if _has_critical_module_data():
                _COV_ENSURED = True
                return True
            if os.path.exists(COVERAGE_FILE):
                os.remove(COVERAGE_FILE)
    except Exception:
        pass
    return False


def _load_coverage_from_api():
    try:
        import coverage as _c
    except ImportError:
        return None
    try:
        cov = _c.Coverage()
        cov.load()
        files = {}
        for fpath in cov.get_data().measured_files():
            try:
                analysis = cov.analysis(fpath)
            except Exception:
                continue
            stmts = list(analysis.statements)
            missing = list(analysis.missing)
            total = len(stmts)
            executed = total - len(missing)
            pct = round(executed / total * 100, 1) if total > 0 else 100.0
            norm = fpath.replace("\\", "/")
            files[norm] = {
                "summary": {
                    "covered_lines": executed,
                    "num_statements": total,
                    "percent_covered": pct,
                    "percent_covered_display": pct,
                    "missing_lines": len(missing),
                    "excluded_lines": 0,
                }
            }
        return {"files": files}
    except Exception:
        return None


def _load_coverage_data():
    if os.path.exists(COVERAGE_JSON):
        with open(COVERAGE_JSON) as f:
            return json.load(f)
    json_result = subprocess.run(
        [sys.executable, "-m", "coverage", "json"],
        capture_output=True, text=True,
        cwd=PROJECT_ROOT, timeout=30,
    )
    if json_result.returncode == 0 and os.path.exists(COVERAGE_JSON):
        with open(COVERAGE_JSON) as f:
            return json.load(f)
    return _load_coverage_from_api()


class TestQRT003CriticalModuleCoverage:

    def test_critical_modules_have_sufficient_coverage(self):
        _cleanup_artifacts()

        if not _ensure_coverage_file():
            assert _run_critical_tests_under_coverage(), (
                "Could not collect coverage for critical modules"
            )

        coverage_data = _load_coverage_data()

        if coverage_data is None:
            pytest.fail("Could not load coverage data")

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
