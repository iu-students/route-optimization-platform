import json
import os
import pytest

import script
import loaders
from verifier import run_verification


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
def run_pipeline(tmp_path, monkeypatch):
    """Run the full script.py pipeline in a temp folder with a short PyVRP runtime."""
    from pyvrp import Model
    from pyvrp.stop import MaxRuntime

    # write input.json in tmp_path
    (tmp_path / "input.json").write_text(json.dumps(SMALL_INPUT))

    # script.py uses fixed filenames ('input.json', 'output.json', 'loaders_task_list.json')
    # and loaders.solve_loaders() also reads 'input.json' — so we cd into tmp_path
    monkeypatch.chdir(tmp_path)

    # reset loaders global state (in case another test ran before)
    loaders.reset_state()

    # build scenario
    scenario_obj = script.parse("input.json")

    # calculate_vehicles_routes uses a module-level `scenario` from script
    script.scenario = scenario_obj

    model = Model()
    script.fill_model(scenario_obj, model)

    result = model.solve(stop=MaxRuntime(2))  # short runtime for CI

    vehicles = script.calculate_vehicles_routes(result, scenario_obj)
    script.create_loaders_task_list(vehicles, scenario_obj)
    loaders_result = loaders.solve_loaders()
    script.build_output(vehicles, loaders_result, scenario_obj)

    with open(tmp_path / "output.json") as f:
        output_data = json.load(f)

    return SMALL_INPUT, output_data


def test_shift_times_pass(run_pipeline):
    input_data, output_data = run_pipeline
    result = run_verification(input_path="input.json", output_path="output.json")
    assert result["shift_verification"]["status"] == "success"


def test_time_windows_pass(run_pipeline):
    input_data, output_data = run_pipeline
    result = run_verification(input_path="input.json", output_path="output.json")
    assert result["time_window_verification"]["status"] == "success"


def test_capacity_pass(run_pipeline):
    input_data, output_data = run_pipeline
    result = run_verification(input_path="input.json", output_path="output.json")
    assert result["capacity_verification"]["status"] == "success"


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


def test_output_has_vehicles(run_pipeline):
    input_data, output_data = run_pipeline
    assert len(output_data["vehicles"]) >= 1