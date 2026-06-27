import json
import os
import shutil
import pytest

from script import solve_pipeline
from verifier import run_verification
from tester import calc_cost

SMALL_INPUT = {
    "vehicle_capacity": 100,
    "vehicle_speed": 1,
    "loader_speed": 1,
    "vehicle_shift_size": 500,
    "loader_shift_size": 500,
    "depot": {"x": 50, "y": 50, "load_time": 5},
    "orders": [
        {"id": 1, "x": 60, "y": 50, "volume": 20, "time_window": [0, 200],
         "vehicle_service_time": 10, "loader_cnt": 1, "loader_service_time": 8, "optional": 0},
        {"id": 2, "x": 40, "y": 50, "volume": 30, "time_window": [0, 200],
         "vehicle_service_time": 10, "loader_cnt": 1, "loader_service_time": 8, "optional": 0},
        {"id": 3, "x": 50, "y": 60, "volume": 25, "time_window": [0, 300],
         "vehicle_service_time": 10, "loader_cnt": 0, "loader_service_time": 0, "optional": 0},
        {"id": 4, "x": 70, "y": 70, "volume": 15, "time_window": [50, 300],
         "vehicle_service_time": 10, "loader_cnt": 1, "loader_service_time": 10, "optional": 0},
        {"id": 5, "x": 30, "y": 30, "volume": 10, "time_window": [0, 400],
         "vehicle_service_time": 5, "loader_cnt": 0, "loader_service_time": 0, "optional": 1},
    ],
    "weights": {
        "optional_order_penalty": 500,
        "vehicle_salary": 100,
        "loader_salary": 50,
        "fuel_cost": 2,
        "loader_work": 1,
    },
}


@pytest.fixture
def run_pipeline(tmp_path):
    """Run solve_pipeline in a temp folder and return (input_data, output_data)."""
    
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(SMALL_INPUT, indent=2))

    import script
    old_runtime = 120

    original = script.solve_pipeline

    def patched(input_path="input.json", data_dir="."):
        import pyvrp.stop
        old_class = pyvrp.stop.MaxRuntime
        orig_init = old_class.__init__

        def fast_init(self, max_runtime):
            orig_init(self, 2)

        old_class.__init__ = fast_init
        try:
            original(input_path, data_dir)
        finally:
            old_class.__init__ = orig_init

    patched(input_path="input.json", data_dir=str(tmp_path))

    # load output
    with open(tmp_path / "output.json") as f:
        output_data = json.load(f)

    return SMALL_INPUT, output_data


def test_shift_times_pass(run_pipeline):
    input_data, output_data = run_pipeline
    verification = output_data["verification"]
    assert verification["shift_verification"]["status"] == "success"


def test_time_windows_pass(run_pipeline):
    input_data, output_data = run_pipeline
    verification = output_data["verification"]
    assert verification["time_window_verification"]["status"] == "success"


def test_capacity_pass(run_pipeline):
    input_data, output_data = run_pipeline
    verification = output_data["verification"]
    assert verification["capacity_verification"]["status"] == "success"


def test_all_required_orders_served(run_pipeline):
    input_data, output_data = run_pipeline
    required = {o["id"] for o in input_data["orders"] if o["optional"] == 0}
    served = set()
    for v in output_data["vehicles"]:
        for p in v["route"]:
            if p != 0:
                served.add(p)
    missing = required - served
    assert missing == set(), f"required orders not served: {missing}"


def test_no_duplicate_orders(run_pipeline):
    input_data, output_data = run_pipeline
    all_served = []
    for v in output_data["vehicles"]:
        for p in v["route"]:
            if p != 0:
                all_served.append(p)
    assert len(all_served) == len(set(all_served)), "some orders are served twice"


def test_output_has_loaders(run_pipeline):
    input_data, output_data = run_pipeline
    
    assert len(output_data["loaders"]) >= 1


def test_cost_is_positive(run_pipeline):
    input_data, output_data = run_pipeline
    result = calc_cost(input_data, output_data)
    assert result["total_cost"] > 0
    assert result["missing_required_ids"] == []
