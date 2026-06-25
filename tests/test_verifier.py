import verifier


def make_input():
    return {
        "vehicle_capacity": 10,
        "vehicle_shift_size": 100,
        "orders": [
            {"id": 1, "x": 0, "y": 0, "volume": 4, "time_window": [0, 50]},
            {"id": 2, "x": 1, "y": 1, "volume": 5, "time_window": [10, 60]},
        ],
    }


def test_shift_ok():
    data = make_input()
    vehicles = [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 20]}]
    result = verifier.verify_shift_times(data, vehicles)
    assert result["status"] == "success"


def test_shift_too_late():
    data = make_input()
    vehicles = [{"id": 1, "route": [0, 1, 0], "time": [120]}]
    result = verifier.verify_shift_times(data, vehicles)
    assert result["status"] == "error"


def test_shift_empty_route():
    data = make_input()
    vehicles = [{"id": 1, "route": [0, 0], "time": []}]
    result = verifier.verify_shift_times(data, vehicles)
    assert result["status"] == "success"


def test_time_windows_ok():
    data = make_input()
    vehicles = [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 20]}]
    result = verifier.verify_time_windows(data, vehicles)
    assert result["status"] == "success"


def test_time_window_too_early():
    data = make_input()
    vehicles = [{"id": 1, "route": [0, 2, 0], "time": [3]}]
    result = verifier.verify_time_windows(data, vehicles)
    assert result["status"] == "error"


def test_time_window_too_late():
    data = make_input()
    vehicles = [{"id": 1, "route": [0, 1, 0], "time": [70]}]
    result = verifier.verify_time_windows(data, vehicles)
    assert result["status"] == "error"


def test_time_window_unknown_order():
    data = make_input()
    vehicles = [{"id": 1, "route": [0, 99, 0], "time": [5]}]
    result = verifier.verify_time_windows(data, vehicles)
    assert result["status"] == "error"


def test_capacity_ok():
    data = make_input()
    vehicles = [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 20]}]
    result = verifier.verify_truck_capacity(data, vehicles)
    assert result["status"] == "success"


def test_capacity_too_big():
    data = make_input()
    data["vehicle_capacity"] = 8
    vehicles = [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 20]}]
    result = verifier.verify_truck_capacity(data, vehicles)
    assert result["status"] == "error"


def test_capacity_two_segments():
    data = make_input()
    vehicles = [{"id": 1, "route": [0, 1, 0, 2, 0], "time": [5, 20]}]
    result = verifier.verify_truck_capacity(data, vehicles)
    assert result["status"] == "success"


def test_split_segments():
    segments = verifier._split_route_into_segments([0, 1, 2, 0, 3, 0])
    assert segments == [[1, 2], [3]]
