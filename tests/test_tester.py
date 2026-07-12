import json
import random
import string
from tester import calc_cost, euclidean, get_coords, export_excel


def make_input():
    return {
        "vehicle_capacity": 100,
        "vehicle_speed": 1,
        "loader_speed": 1,
        "vehicle_shift_size": 480,
        "loader_shift_size": 480,
        "weights": {
            "vehicle_salary": 100,
            "loader_salary": 50,
            "fuel_cost": 2,
            "loader_work": 1,
            "optional_order_penalty": 1000,
        },
        "depot": {"x": 0, "y": 0},
        "orders": [
            {"id": 1, "x": 3, "y": 4, "volume": 5, "loader_service_time": 10, "optional": 0},
            {"id": 2, "x": 0, "y": 0, "volume": 5, "loader_service_time": 20, "optional": 0},
            {"id": 3, "x": 1, "y": 1, "volume": 2, "loader_service_time": 5, "optional": 1},
        ],
    }


def test_euclidean():
    assert euclidean((0, 0), (3, 4)) == 5.0


def test_get_coords_depot():
    assert get_coords(0, {"x": 7, "y": 9}, {}) == (7, 9)


def test_get_coords_order():
    orders_by_id = {1: {"x": 2, "y": 5}}
    assert get_coords(1, {"x": 0, "y": 0}, orders_by_id) == (2, 5)


def test_counts_and_costs():
    data = make_input()
    output = {
        "vehicles": [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 9]}],
        "loaders": [{"id": 1, "route": [1, 2]}],
    }
    result = calc_cost(data, output)
    assert result["n_vehicles"] == 1
    assert result["cost"]["vehicles"] == 100
    assert result["n_loaders"] == 1
    assert result["cost"]["loaders"] == 50


def test_optional_penalty():
    data = make_input()
    output = {
        "vehicles": [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 9]}],
        "loaders": [],
    }
    result = calc_cost(data, output)
    assert result["missed_optional"] == [3]
    assert result["cost"]["penalty"] == 1000


def test_missing_required():
    data = make_input()
    output = {
        "vehicles": [{"id": 1, "route": [0, 1, 0], "time": [5.0]}],
        "loaders": [],
    }
    result = calc_cost(data, output)
    assert result["missed_mandatory"] == [2]


def test_total_cost_is_sum_of_components():
    data = make_input()
    output = {
        "vehicles": [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 9]}],
        "loaders": [{"id": 1, "route": [1]}],
    }
    result = calc_cost(data, output)
    c = result["cost"]
    expected = c["vehicles"] + c["loaders"] + c["fuel"] + c["loader_w"] + c["penalty"]
    assert c["total"] == expected


def test_export_excel(tmp_path):
    """export_excel must produce a non-empty file."""
    data = make_input()
    output = {
        "vehicles": [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 9]}],
        "loaders": [{"id": 1, "route": [1, 2]}],
    }
    result = calc_cost(data, output)
    results_dict = {"BASELINE": result, "OUR": result}
    out_path = tmp_path / "report.xlsx"
    export_excel(results_dict, str(out_path))
    assert out_path.exists()
    assert out_path.stat().st_size > 0
