import json
import pytest

import main
from validator import validate_input
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
def run_cpsat_pipeline(tmp_path, monkeypatch):
    """Run main.py pipeline (CP-SAT) in a temp folder with few restarts."""
    # main.find_vehicles_routes and find_loaders_routes write JSON files
    # ('all_possible_vehicles_routes.json', 'all_possible_loaders_routes.json')
    # in the current dir — so we cd into tmp_path.
    monkeypatch.chdir(tmp_path)

    # write input.json (for verifier later)
    (tmp_path / "input.json").write_text(json.dumps(SMALL_INPUT))

    # build scenario directly, skipping main.parse (which reads from disk)
    from models import Scenario, Depot, Weights, Order
    validate_input(SMALL_INPUT)
    scenario = Scenario(
        depot=Depot(**SMALL_INPUT["depot"]),
        weights=Weights(**SMALL_INPUT["weights"]),
        orders=[Order(**o) for o in SMALL_INPUT["orders"]],
        vehicle_capacity=SMALL_INPUT["vehicle_capacity"],
        vehicle_speed=SMALL_INPUT["vehicle_speed"],
        loader_speed=SMALL_INPUT["loader_speed"],
        vehicle_shift_size=SMALL_INPUT["vehicle_shift_size"],
        loader_shift_size=SMALL_INPUT["loader_shift_size"],
    )

    # few restarts → fast for CI
    solution = main.find_vehicles_routes(scenario, num_restarts=3)
    solution["loaders"] = main.find_loaders_routes(solution, scenario, num_restarts=3)

    # normalize key for verifier compatibility
    # main uses "vehicle_id" but verifier expects "id"
    for v in solution["vehicles"]:
        if "vehicle_id" in v and "id" not in v:
            v["id"] = v["vehicle_id"]

    # write output.json for verifier
    (tmp_path / "output.json").write_text(json.dumps(solution))

    return SMALL_INPUT, solution


def test_cpsat_shift_times_pass(run_cpsat_pipeline):
    result = run_verification(input_path="input.json", output_path="output.json")
    assert result["shift_verification"]["status"] == "success"


def test_cpsat_time_windows_pass(run_cpsat_pipeline):
    result = run_verification(input_path="input.json", output_path="output.json")
    assert result["time_window_verification"]["status"] == "success"


def test_cpsat_capacity_pass(run_cpsat_pipeline):
    result = run_verification(input_path="input.json", output_path="output.json")
    assert result["capacity_verification"]["status"] == "success"


def test_cpsat_all_required_orders_served(run_cpsat_pipeline):
    input_data, solution = run_cpsat_pipeline
    required = {o["id"] for o in input_data["orders"] if o["optional"] == 0}
    served = set()
    for v in solution["vehicles"]:
        for p in v["route"]:
            if p != 0:
                served.add(p)
    missing = required - served
    assert missing == set(), f"required orders not served: {missing}"


def test_cpsat_no_duplicate_orders(run_cpsat_pipeline):
    _, solution = run_cpsat_pipeline
    all_served = []
    for v in solution["vehicles"]:
        for p in v["route"]:
            if p != 0:
                all_served.append(p)
    assert len(all_served) == len(set(all_served))


def test_cpsat_output_has_vehicles(run_cpsat_pipeline):
    _, solution = run_cpsat_pipeline
    assert len(solution["vehicles"]) >= 1