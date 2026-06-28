import json
import pytest
import validator
from validator import ValidationError, validate_input


def make_valid_input():
    return {
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
            {"id": 1, "x": 10, "y": 10, "volume": 5,
             "time_window": [0, 100], "vehicle_service_time": 5,
             "loader_cnt": 0, "loader_service_time": 0, "optional": 0},
        ],
    }


def test_valid_input_passes():
    assert validate_input(make_valid_input()) == {"status": "ok"}


def test_root_must_be_object():
    with pytest.raises(ValidationError) as exc:
        validate_input([])
    assert any("Root must be an object" in e["message"] for e in exc.value.errors)


# depot

def test_missing_depot():
    data = make_valid_input()
    del data["depot"]
    with pytest.raises(ValidationError) as exc:
        validate_input(data)
    assert any(e["path"] == "depot" for e in exc.value.errors)


def test_depot_not_object():
    data = make_valid_input()
    data["depot"] = "not an object"
    with pytest.raises(ValidationError):
        validate_input(data)


def test_depot_missing_fields():
    data = make_valid_input()
    data["depot"] = {"x": 0}
    with pytest.raises(ValidationError) as exc:
        validate_input(data)
    paths = [e["path"] for e in exc.value.errors]
    assert "depot.y" in paths
    assert "depot.load_time" in paths


def test_depot_x_not_number():
    data = make_valid_input()
    data["depot"]["x"] = "abc"
    with pytest.raises(ValidationError):
        validate_input(data)


def test_depot_load_time_negative():
    data = make_valid_input()
    data["depot"]["load_time"] = -1
    with pytest.raises(ValidationError):
        validate_input(data)


# weights

def test_weights_missing_field():
    data = make_valid_input()
    del data["weights"]["fuel_cost"]
    with pytest.raises(ValidationError) as exc:
        validate_input(data)
    assert any(e["path"] == "weights.fuel_cost" for e in exc.value.errors)


def test_weights_field_not_number():
    data = make_valid_input()
    data["weights"]["loader_salary"] = "free"
    with pytest.raises(ValidationError):
        validate_input(data)


def test_weights_field_negative():
    data = make_valid_input()
    data["weights"]["loader_salary"] = -10
    with pytest.raises(ValidationError):
        validate_input(data)


# orders

def test_orders_not_list():
    data = make_valid_input()
    data["orders"] = "not a list"
    with pytest.raises(ValidationError):
        validate_input(data)


def test_orders_empty():
    data = make_valid_input()
    data["orders"] = []
    with pytest.raises(ValidationError):
        validate_input(data)


def test_order_missing_field():
    data = make_valid_input()
    del data["orders"][0]["volume"]
    with pytest.raises(ValidationError) as exc:
        validate_input(data)
    assert any(e["path"] == "orders[0].volume" for e in exc.value.errors)


def test_order_volume_negative():
    data = make_valid_input()
    data["orders"][0]["volume"] = -5
    with pytest.raises(ValidationError):
        validate_input(data)


def test_order_time_window_wrong_size():
    data = make_valid_input()
    data["orders"][0]["time_window"] = [0]
    with pytest.raises(ValidationError):
        validate_input(data)


def test_order_time_window_not_numbers():
    data = make_valid_input()
    data["orders"][0]["time_window"] = ["a", "b"]
    with pytest.raises(ValidationError):
        validate_input(data)


def test_order_time_window_negative():
    data = make_valid_input()
    data["orders"][0]["time_window"] = [-10, 50]
    with pytest.raises(ValidationError):
        validate_input(data)


def test_order_time_window_start_after_end():
    data = make_valid_input()
    data["orders"][0]["time_window"] = [100, 50]
    with pytest.raises(ValidationError):
        validate_input(data)


def test_order_optional_not_zero_or_one():
    data = make_valid_input()
    data["orders"][0]["optional"] = 2
    with pytest.raises(ValidationError):
        validate_input(data)


def test_order_duplicate_ids():
    data = make_valid_input()
    data["orders"].append({
        "id": 1, "x": 20, "y": 20, "volume": 1,
        "time_window": [0, 100], "vehicle_service_time": 1,
        "loader_cnt": 0, "loader_service_time": 0, "optional": 0,
    })
    with pytest.raises(ValidationError) as exc:
        validate_input(data)
    assert any("Duplicate id" in e["message"] for e in exc.value.errors)


# top-level positive fields

def test_vehicle_capacity_zero():
    data = make_valid_input()
    data["vehicle_capacity"] = 0
    with pytest.raises(ValidationError):
        validate_input(data)


def test_vehicle_speed_negative():
    data = make_valid_input()
    data["vehicle_speed"] = -1
    with pytest.raises(ValidationError):
        validate_input(data)


def test_loader_shift_size_zero():
    data = make_valid_input()
    data["loader_shift_size"] = 0
    with pytest.raises(ValidationError):
        validate_input(data)


# validate_file

def test_validate_file_ok(tmp_path):
    f = tmp_path / "input.json"
    f.write_text(json.dumps(make_valid_input()))
    assert validator.validate_file(str(f)) == {"status": "ok"}


def test_validate_file_invalid_json(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{not valid json")
    with pytest.raises(ValidationError) as exc:
        validator.validate_file(str(f))
    assert any("Invalid JSON" in e["message"] for e in exc.value.errors)


def test_multiple_errors_collected():
    data = make_valid_input()
    data["vehicle_capacity"] = -1
    data["orders"][0]["volume"] = -5
    with pytest.raises(ValidationError) as exc:
        validate_input(data)
    assert len(exc.value.errors) >= 2