import json
from typing import List


def _split_route_into_segments(route: List[int]) -> List[List[int]]:
    segments = []
    current = []
    for point in route:
        if point == 0:
            if current:
                segments.append(current)
                current = []
        else:
            current.append(point)
    if current:
        segments.append(current)
    return segments


def verify_shift_times(input_data: dict, vehicles: list) -> dict:
    shift_end = input_data["vehicle_shift_size"]

    all_ok = True
    vehicle_results = []

    for vehicle in vehicles:
        route = vehicle["route"]
        times = vehicle["time"]

        delivery_points = [p for p in route if p != 0]
        if not delivery_points:
            vehicle_results.append({
                "vehicle_id": vehicle["id"],
                "status": "success",
                "message": "Empty route (no shift constraint violation)",
            })
            continue

        route_start_time = times[0]

        if round(route_start_time, 2) <= round(shift_end, 2):
            vehicle_results.append({
                "vehicle_id": vehicle["id"],
                "status": "success",
                "message": (
                    f"Route start {route_start_time} <= shift end {shift_end}"
                ),
                "route_start_time": route_start_time,
                "shift_end": shift_end,
            })
        else:
            all_ok = False
            vehicle_results.append({
                "vehicle_id": vehicle["id"],
                "status": "error",
                "message": (
                    f"Route start {route_start_time} > shift end {shift_end}"
                ),
                "route_start_time": route_start_time,
                "shift_end": shift_end,
            })

    return {
        "status": "success" if all_ok else "error",
        "vehicles": vehicle_results,
    }


def verify_time_windows(input_data: dict, vehicles: list) -> dict:
    orders_by_id = {o["id"]: o for o in input_data["orders"]}

    all_ok = True
    vehicle_results = []

    for vehicle in vehicles:
        route = vehicle["route"]
        times = vehicle["time"]

        delivery_points = [p for p in route if p != 0]
        if not delivery_points:
            vehicle_results.append({
                "vehicle_id": vehicle["id"],
                "status": "success",
                "message": "Empty route (no time window violations)",
            })
            continue

        vehicle_ok = True
        point_details = []

        for i, order_id in enumerate(delivery_points):
            arrival_time = times[i]
            order = orders_by_id.get(order_id)
            if order is None:
                vehicle_ok = False
                all_ok = False
                point_details.append({
                    "order_id": order_id,
                    "arrival_time": arrival_time,
                    "status": "error",
                    "message": f"Order {order_id} not found in input data",
                })
                continue

            tw_start, tw_end = order["time_window"]

            if round(arrival_time, 2) < round(tw_start, 2):
                vehicle_ok = False
                all_ok = False
                point_details.append({
                    "order_id": order_id,
                    "arrival_time": arrival_time,
                    "time_window": [tw_start, tw_end],
                    "status": "error",
                    "message": (
                        f"Arrival {arrival_time} "
                        f"before time window start {tw_start}"
                    ),
                })
            elif round(arrival_time, 2) > round(tw_end, 2):
                vehicle_ok = False
                all_ok = False
                point_details.append({
                    "order_id": order_id,
                    "arrival_time": arrival_time,
                    "time_window": [tw_start, tw_end],
                    "status": "error",
                    "message": (
                        f"Arrival {arrival_time} "
                        f"after time window end {tw_end}"
                    ),
                })
            else:
                point_details.append({
                    "order_id": order_id,
                    "arrival_time": arrival_time,
                    "time_window": [tw_start, tw_end],
                    "status": "success",
                    "message": (
                        f"Arrival {arrival_time} within [{tw_start}, {tw_end}]"
                    ),
                })

        vehicle_results.append({
            "vehicle_id": vehicle["id"],
            "status": "success" if vehicle_ok else "error",
            "points": point_details,
        })

    return {
        "status": "success" if all_ok else "error",
        "vehicles": vehicle_results,
    }


def verify_truck_capacity(input_data: dict, vehicles: list) -> dict:
    vehicle_capacity = input_data["vehicle_capacity"]
    orders_by_id = {o["id"]: o for o in input_data["orders"]}

    all_ok = True
    vehicle_results = []

    for vehicle in vehicles:
        route = vehicle["route"]
        segments = _split_route_into_segments(route)

        if not segments:
            vehicle_results.append({
                "vehicle_id": vehicle["id"],
                "status": "success",
                "message": "Empty route (0 <= capacity)",
                "segments": [],
                "max_capacity": vehicle_capacity,
            })
            continue

        vehicle_ok = True
        segment_details = []

        for seg_idx, segment in enumerate(segments):
            total_volume = sum(orders_by_id[oid]["volume"] for oid in segment)

            if total_volume < 0:
                vehicle_ok = False
                all_ok = False
                segment_details.append({
                    "segment_index": seg_idx,
                    "order_ids": segment,
                    "total_volume": total_volume,
                    "capacity": vehicle_capacity,
                    "status": "error",
                    "message": f"Negative total volume ({total_volume})",
                })
            elif round(total_volume, 2) > round(vehicle_capacity, 2):
                vehicle_ok = False
                all_ok = False
                segment_details.append({
                    "segment_index": seg_idx,
                    "order_ids": segment,
                    "total_volume": total_volume,
                    "capacity": vehicle_capacity,
                    "status": "error",
                    "message": (
                        f"Volume {total_volume} "
                        f"exceeds capacity {vehicle_capacity}"
                    ),
                })
            else:
                segment_details.append({
                    "segment_index": seg_idx,
                    "order_ids": segment,
                    "total_volume": total_volume,
                    "capacity": vehicle_capacity,
                    "status": "success",
                    "message": (
                        f"Volume {total_volume} <= capacity {vehicle_capacity}"
                    ),
                })

        vehicle_results.append({
            "vehicle_id": vehicle["id"],
            "status": "success" if vehicle_ok else "error",
            "segments": segment_details,
            "max_capacity": vehicle_capacity,
        })

    return {
        "status": "success" if all_ok else "error",
        "vehicles": vehicle_results,
    }


def run_verification(
    input_path: str = "data/input.json",
    output_path: str = "data/output.json",
) -> dict:
    with open(input_path) as f:
        input_data = json.load(f)
    with open(output_path) as f:
        output_data = json.load(f)

    vehicles = output_data["vehicles"]

    shift_result = verify_shift_times(input_data, vehicles)
    time_window_result = verify_time_windows(input_data, vehicles)
    capacity_result = verify_truck_capacity(input_data, vehicles)

    return {
        "shift_verification": shift_result,
        "time_window_verification": time_window_result,
        "capacity_verification": capacity_result,
    }


if __name__ == "__main__":
    result = run_verification()
    print(json.dumps(result, indent=2, ensure_ascii=False))
