import json
import script
import pytest
from validator import ValidationError

def test_find_distance():
    assert script.find_distance(0, 0, 3, 4) == 5.0


def test_find_distance_same_point():
    assert script.find_distance(2, 2, 2, 2) == 0.0


def test_compute_times(scenario):
    times = script.compute_times([1], scenario)
    assert times == [5.0]


def test_compute_times_respects_window():
    from models import Scenario, Depot, Weights, Order
    depot = Depot(x=0, y=0, load_time=0)
    weights = Weights(1000, 100, 50, 2, 1)
    orders = [Order(id=1, x=1, y=0, volume=1, time_window=(40, 80),
                    vehicle_service_time=0, loader_cnt=0, loader_service_time=0, optional=0)]
    sc = Scenario(10, 1, 1, 100, 100, depot, weights, orders)
    
    assert script.compute_times([1], sc) == [40.0]


def test_create_loaders_task_list(tmp_path, scenario):
    vehicles = [{
        "id": 1,
        "route": [0, 1, 2, 0],
        "time": [5, 12],
        "time2": 20,
    }]
    script.create_loaders_task_list(vehicles, scenario, data_dir=str(tmp_path))

    with open(tmp_path / "loaders_task_list.json") as f:
        data = json.load(f)

    points = data["routes"][0]["points"]
    assert len(points) == 1
    assert points[0]["id"] == 1


def test_build_output(tmp_path):
    class FakePoint:
        def __init__(self, pid):
            self.point_id = pid

    class FakeLoader:
        def __init__(self, ids):
            self.route = [FakePoint(i) for i in ids]

    vehicles = [{"id": 1, "route": [0, 1, 0], "time": [5]}]
    loaders_result = [FakeLoader([1, 1])]

    script.build_output(vehicles, loaders_result, None, data_dir=str(tmp_path))

    with open(tmp_path / "output.json") as f:
        data = json.load(f)

    assert data["vehicles"][0]["id"] == 1
    assert data["loaders"][0]["route"] == [1, 1]

def test_parse_rejects_invalid_input(tmp_path):
    bad_input = {
        "vehicle_capacity": -1,  # must be > 0
        "vehicle_speed": 3,
        "loader_speed": 1,
        "vehicle_shift_size": 720,
        "loader_shift_size": 720,
        "depot": {"x": 0, "y": 0, "load_time": 0},
        "weights": {
            "optional_order_penalty": 100, "vehicle_salary": 100,
            "loader_salary": 50, "fuel_cost": 1, "loader_work": 1,
        },
        "orders": [
            {"id": 1, "x": 1, "y": 1, "volume": 1, "time_window": [0, 100],
             "vehicle_service_time": 1, "loader_cnt": 0,
             "loader_service_time": 0, "optional": 0},
        ],
    }
    f = tmp_path / "bad.json"
    f.write_text(json.dumps(bad_input))

    with pytest.raises(ValidationError):
        script.parse(str(f))


def test_parse_accepts_valid_input(tmp_path):
    good_input = {
        "vehicle_capacity": 100,
        "vehicle_speed": 3,
        "loader_speed": 1,
        "vehicle_shift_size": 720,
        "loader_shift_size": 720,
        "depot": {"x": 0, "y": 0, "load_time": 0},
        "weights": {
            "optional_order_penalty": 100, "vehicle_salary": 100,
            "loader_salary": 50, "fuel_cost": 1, "loader_work": 1,
        },
        "orders": [
            {"id": 1, "x": 1, "y": 1, "volume": 1, "time_window": [0, 100],
             "vehicle_service_time": 1, "loader_cnt": 0,
             "loader_service_time": 0, "optional": 0},
        ],
    }
    f = tmp_path / "good.json"
    f.write_text(json.dumps(good_input))

    scenario_obj = script.parse(str(f))
    assert scenario_obj.vehicle_capacity == 100
    assert len(scenario_obj.orders) == 1
