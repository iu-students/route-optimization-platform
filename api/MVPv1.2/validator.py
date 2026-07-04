import json


class ValidationError(Exception):
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(f"Validation failed: {len(errors)} error(s)")

    def to_dict(self) -> dict:
        return {"detail": "Input validation failed", "errors": self.errors}


def is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_input(data) -> dict:
    errors = []

    if not isinstance(data, dict):
        raise ValidationError(
            [{"path": "", "message": "Root must be an object"}])

    top_fields = [
        "depot", "orders", "weights",
        "vehicle_capacity", "vehicle_speed", "loader_speed",
        "vehicle_shift_size", "loader_shift_size",
    ]

    for f in top_fields:
        if f not in data:
            errors.append({"path": f, "message": "Missing required field"})

    if "depot" in data:
        depot = data["depot"]
        if not isinstance(depot, dict):
            errors.append({"path": "depot", "message": "Must be an object"})
        else:
            for f in ["x", "y", "load_time"]:
                if f not in depot:
                    errors.append(
                        {"path": f"depot.{f}",
                         "message": "Missing required field"})

            for f in ["x", "y"]:
                if f in depot and not is_number(depot[f]):
                    errors.append(
                        {"path": f"depot.{f}",
                         "message": "Must be a number"})

            if "load_time" in depot:
                lt = depot["load_time"]
                if not is_number(lt):
                    errors.append(
                        {"path": "depot.load_time",
                         "message": "Must be a number"})
                elif lt < 0:
                    errors.append(
                        {"path": "depot.load_time",
                         "message": f"Must be >= 0, got {lt}"})

    if "weights" in data:
        weights = data["weights"]
        weights_fields = [
            "vehicle_salary", "loader_salary",
            "optional_order_penalty", "fuel_cost", "loader_work",
        ]

        if not isinstance(weights, dict):
            errors.append({"path": "weights", "message": "Must be an object"})
        else:
            for f in weights_fields:
                if f not in weights:
                    errors.append(
                        {"path": f"weights.{f}",
                         "message": "Missing required field"})
                    continue
                wf = weights[f]
                if not is_number(wf):
                    errors.append(
                        {"path": f"weights.{f}",
                         "message": "Must be a number"})
                elif wf < 0:
                    errors.append(
                        {"path": f"weights.{f}",
                         "message": f"Must be >= 0, got {wf}"})

    if "orders" in data:
        orders = data["orders"]
        order_fields = [
            "id", "x", "y", "volume", "time_window",
            "vehicle_service_time", "loader_cnt",
            "loader_service_time", "optional",
        ]

        if not isinstance(orders, list):
            errors.append({"path": "orders", "message": "Must be a list"})
        elif len(orders) == 0:
            errors.append(
                {"path": "orders",
                 "message": "Must contain at least one order"})
        else:
            ids_seen = set()

            for i, order in enumerate(orders):
                path = f"orders[{i}]"

                if not isinstance(order, dict):
                    errors.append(
                        {"path": path,
                         "message": "Must be an object"})
                    continue

                for f in order_fields:
                    if f not in order:
                        errors.append(
                            {"path": f"{path}.{f}",
                             "message": "Missing required field"})

                for f in ["id", "x", "y"]:
                    if f in order and not is_number(order[f]):
                        errors.append(
                            {"path": f"{path}.{f}",
                             "message": "Must be a number"})

                num_fields = [
                    "volume", "loader_cnt",
                    "vehicle_service_time", "loader_service_time",
                ]
                for f in num_fields:
                    if f in order:
                        v = order[f]
                        if not is_number(v):
                            errors.append(
                                {"path": f"{path}.{f}",
                                 "message": "Must be a number"})
                        elif v < 0:
                            errors.append(
                                {"path": f"{path}.{f}",
                                 "message": f"Must be >= 0, got {v}"})

                if "time_window" in order:
                    tw = order["time_window"]
                    tw_path = f"{path}.time_window"

                    if not isinstance(tw, list) or len(tw) != 2:
                        errors.append(
                            {"path": tw_path,
                             "message": "Must be array of 2 numbers"})
                    elif not is_number(tw[0]) or not is_number(tw[1]):
                        errors.append(
                            {"path": tw_path,
                             "message": "Both values must be numbers"})
                    else:
                        if tw[0] < 0 or tw[1] < 0:
                            errors.append(
                                {"path": tw_path,
                                 "message": f"Values must be >= 0, got {tw}"})
                        if tw[0] > tw[1]:
                            errors.append(
                                {"path": tw_path,
                                 "message": f"Start ({tw[0]}) must be "
                                 f"<= end ({tw[1]})"})

                if "optional" in order and order["optional"] not in (0, 1):
                    errors.append(
                        {"path": f"{path}.optional",
                         "message": "Must be 0 or 1, "
                         f"got {order['optional']!r}"})

                if "id" in order:
                    oid = order["id"]
                    if oid in ids_seen:
                        errors.append(
                            {"path": f"{path}.id",
                             "message": f"Duplicate id {oid}"})
                    ids_seen.add(oid)

    positive_fields = [
        "vehicle_capacity", "vehicle_speed", "loader_speed",
        "vehicle_shift_size", "loader_shift_size",
    ]

    for f in positive_fields:
        if f in data:
            if not is_number(data[f]):
                errors.append({"path": f, "message": "Must be a number"})
            elif data[f] <= 0:
                errors.append(
                    {"path": f,
                     "message": f"Must be > 0, got {data[f]}"})

    if errors:
        raise ValidationError(errors)

    return {"status": "ok"}


def validate_file(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(
                [{"path": "", "message": f"Invalid JSON: {e}"}])

    return validate_input(data)


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "input.json"

    try:
        validate_file(target)
        print("OK")
    except ValidationError as e:
        print(json.dumps(e.to_dict(), indent=2, ensure_ascii=False))
        sys.exit(1)
