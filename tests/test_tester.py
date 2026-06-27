import tester
import json


def make_input():
    return {
        "vehicle_capacity": 100,
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
    result = tester.compute(data, output)
    assert result["n_vehicles"] == 1
    assert result["cost"]["vehicles"] == 100
    assert result["n_loaders"] == 1
    assert result["cost"]["loaders"] == 50
    # loader_work_time = sum of loader_service_time on each visited order in loader routes
    # loader 1 visits orders 1 and 2 → 10 + 20 = 30
    assert result["loader_work_time"] == 30


def test_optional_penalty():
    data = make_input()
    output = {
        "vehicles": [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 9]}],
        "loaders": [],
    }
    result = tester.compute(data, output)
    # order 3 is optional and not served
    assert result["missed_optional"] == [3]
    assert result["cost"]["penalty"] == 1000


def test_missing_required():
    data = make_input()
    output = {
        "vehicles": [{"id": 1, "route": [0, 1, 0]}],
        "loaders": [],
    }
    result = tester.compute(data, output)
    # order 2 is mandatory and not served
    assert result["missed_mandatory"] == [2]


def test_total_cost_is_sum_of_components():
    data = make_input()
    output = {
        "vehicles": [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 9]}],
        "loaders": [{"id": 1, "route": [1]}],
    }
    result = tester.compute(data, output)
    c = result["cost"]
    expected = c["vehicles"] + c["loaders"] + c["fuel"] + c["loader_w"] + c["penalty"]
    assert c["total"] == expected


def test_print_scenario_with_results(capsys):
    """print_scenario writes to stdout; just check it runs without error."""
    data = make_input()
    output = {
        "vehicles": [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 9]}],
        "loaders": [{"id": 1, "route": [1, 2]}],
    }
    result = tester.compute(data, output)
    tester.print_scenario("test_case", {"BASELINE": result})
    captured = capsys.readouterr()
    assert "test_case".upper() in captured.out
    assert "BASELINE" in captured.out


def test_print_scenario_empty():
    tester.print_scenario("empty", {})  # should not crash


def test_print_scenario_with_diff(capsys):
    """When both BASELINE and another solution exist, diff lines are printed."""
    data = make_input()
    output_a = {
        "vehicles": [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 9]}],
        "loaders": [{"id": 1, "route": [1, 2]}],
    }
    output_b = {
        "vehicles": [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 9]}],
        "loaders": [],
    }
    r_a = tester.compute(data, output_a)
    r_b = tester.compute(data, output_b)
    tester.print_scenario("cmp", {"BASELINE": r_a, "НАШЕ": r_b})
    captured = capsys.readouterr()
    assert "Δ" in captured.out  # diff symbol


def test_analyze_scenario_missing_file(tmp_path):
    inp, res = tester.analyze_scenario("nonexistent", dir_path=str(tmp_path))
    assert inp is None
    assert res == {}


def test_analyze_scenario_reads_input(tmp_path):
    data = {
        "vehicle_capacity": 100,
        "weights": {
            "vehicle_salary": 100, "loader_salary": 50,
            "fuel_cost": 2, "loader_work": 1, "optional_order_penalty": 1000,
        },
        "depot": {"x": 0, "y": 0},
        "orders": [
            {"id": 1, "x": 1, "y": 1, "volume": 1,
             "loader_service_time": 5, "optional": 0},
        ],
    }
    (tmp_path / "t1.json").write_text(json.dumps(data))
    inp, res = tester.analyze_scenario("t1", dir_path=str(tmp_path))
    assert inp is not None
    assert inp["vehicle_capacity"] == 100
    # no solution files exist → results dict is empty
    assert res == {}


def test_export_excel(tmp_path):
    """Smoke test: export_excel must produce a non-empty file."""
    data = make_input()
    output = {
        "vehicles": [{"id": 1, "route": [0, 1, 2, 0], "time": [5, 9]}],
        "loaders": [{"id": 1, "route": [1, 2]}],
    }
    result = tester.compute(data, output)
    all_data = {"t1": (data, {"BASELINE": result, "НАШЕ": result})}
    out_path = tmp_path / "report.xlsx"
    tester.export_excel(all_data, str(out_path))
    assert out_path.exists()
    assert out_path.stat().st_size > 0
