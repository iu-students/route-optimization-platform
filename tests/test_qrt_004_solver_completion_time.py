import json
import os
import sys
import time
import pytest

_BASE = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "api", "MVPv2.2", "CP-SAT"))
sys.path.insert(0, _BASE)

try:
    import main as cpsat_main
except ImportError:
    cpsat_main = None


SAMPLE_INPUT = {
    "vehicle_capacity": 100,
    "vehicle_speed": 3,
    "loader_speed": 1,
    "vehicle_shift_size": 720,
    "loader_shift_size": 720,
    "depot": {"x": 50, "y": 50, "load_time": 10},
    "weights": {
        "optional_order_penalty": 250,
        "vehicle_salary": 200,
        "loader_salary": 200,
        "fuel_cost": 2,
        "loader_work": 1,
    },
    "orders": [
        {"id": 1, "x": 10, "y": 10, "volume": 5, "time_window": [0, 100],
         "vehicle_service_time": 5, "loader_cnt": 0, "loader_service_time": 0, "optional": 0},
        {"id": 2, "x": 30, "y": 40, "volume": 10, "time_window": [0, 200],
         "vehicle_service_time": 5, "loader_cnt": 0, "loader_service_time": 0, "optional": 0},
        {"id": 3, "x": 60, "y": 20, "volume": 8, "time_window": [0, 300],
         "vehicle_service_time": 5, "loader_cnt": 0, "loader_service_time": 0, "optional": 0},
        {"id": 4, "x": 90, "y": 90, "volume": 3, "time_window": [0, 400],
         "vehicle_service_time": 5, "loader_cnt": 0, "loader_service_time": 0, "optional": 0},
        {"id": 5, "x": 5, "y": 80, "volume": 6, "time_window": [0, 500],
         "vehicle_service_time": 5, "loader_cnt": 0, "loader_service_time": 0, "optional": 0},
    ],
}


def _stub_on_stage(name):
    pass


class TestQRT004SolverCompletionTime:

    def test_solver_completes_within_time_limit(self, tmp_path):
        if cpsat_main is None:
            pytest.skip("CP-SAT solver module not importable")

        input_path = tmp_path / "input.json"
        output_path = tmp_path / "output.json"

        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_INPUT, f, indent=2)

        start = time.time()
        try:
            cpsat_main.solve_pipeline(
                input_path=str(input_path),
                output_path=str(output_path),
                on_stage=_stub_on_stage,
            )
        except Exception as e:
            elapsed = time.time() - start
            assert elapsed < 900, (
                f"Solver failed but also exceeded 900s limit: {e}"
            )
            pytest.fail(f"Solver raised an exception: {e}")

        elapsed = time.time() - start
        assert elapsed < 900, (
            f"Solver took {elapsed:.1f}s, expected < 900s"
        )
        assert output_path.exists(), "Output file was not created"

        with open(output_path, encoding="utf-8") as f:
            solution = json.load(f)

        assert "vehicles" in solution, "Solution missing 'vehicles'"
        assert len(solution["vehicles"]) > 0, "No vehicle routes produced"
