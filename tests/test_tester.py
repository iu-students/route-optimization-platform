import tester


def make_input():
    return {
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
    assert tester.euclidean((0, 0), (3, 4)) == 5.0


def test_get_coords_depot():
    assert tester.get_coords(0, {"x": 7, "y": 9}, {}) == (7, 9)


def test_get_coords_order():
    orders_by_id = {1: {"x": 2, "y": 5}}
    assert tester.get_coords(1, {"x": 0, "y": 0}, orders_by_id) == (2, 5)


def test_counts_and_costs():
    data = make_input()
    output = {
        "vehicles": [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 9]}],
        "loaders": [{"id": 1, "route": [1, 2]}],
    }
    result = tester.calc_cost(data, output)
    assert result["n_vehicles"] == 1
    assert result["vehicles_cost"] == 100
    assert result["n_loaders"] == 1
    assert result["loaders_cost"] == 50
    assert result["total_loader_work_time"] == 30


def test_optional_penalty():
    data = make_input()
    output = {
        "vehicles": [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 9]}],
        "loaders": [],
    }
    result = tester.calc_cost(data, output)
    assert result["n_unfulfilled_optional"] == 1
    assert result["optional_penalty_cost"] == 1000


def test_missing_required():
    data = make_input()
    output = {
        "vehicles": [{"id": 1, "route": [0, 1, 0]}],
        "loaders": [],
    }
    result = tester.calc_cost(data, output)
    assert result["missing_required_ids"] == [2]
