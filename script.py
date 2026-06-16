import json
import math

from pyvrp import Model
from pyvrp.stop import MaxRuntime
from loaders import solve_loaders
from models import Scenario, Depot, Weights, Order


def parse(path: str) -> Scenario:
    with open(path) as f:
        raw = json.load(f)
        depot = Depot(**raw["depot"])
    weights = Weights(**raw["weights"])
    orders = [Order(**o) for o in raw["orders"]]

    return Scenario(
        depot=depot,
        weights=weights,
        orders=orders,
        vehicle_capacity=raw["vehicle_capacity"],
        vehicle_speed=raw["vehicle_speed"],
        loader_speed=raw["loader_speed"],
        vehicle_shift_size=raw["vehicle_shift_size"],
        loader_shift_size=raw["loader_shift_size"],
    )


def find_distance(x1, y1, x2, y2) -> float:
    return round(math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2), 2)


def compute_times(order_ids: list, scenario: Scenario) -> list:
    by_id = {order.id: order for order in scenario.orders}

    time = 0.0
    times = []
    px, py = scenario.depot.x, scenario.depot.y

    for order_id in order_ids:
        order = by_id[order_id]

        time += find_distance(px, py, order.x, order.y) / scenario.vehicle_speed
        time = max(time, order.time_window[0])
        times.append(round(time, 2))
        time += order.vehicle_service_time
        px, py = order.x, order.y

    return times


def fill_model(scenario, model):
    coordinates = [(scenario.depot.x, scenario.depot.y)] + [(order.x, order.y) for order in scenario.orders]

    depot = model.add_depot(x=scenario.depot.x, y=scenario.depot.y, tw_early=0)

    clients = []

    for order in scenario.orders:
        c = model.add_client(x=order.x, y=order.y, delivery=order.volume, service_duration=order.vehicle_service_time,
                             tw_early=order.time_window[0], tw_late=order.time_window[1],
                             prize=scenario.weights.optional_order_penalty if order.optional else 0,
                             required=not bool(order.optional))

        clients.append(c)

    all_nodes = [depot] + clients

    for i, (node_i, (x_i, y_i)) in enumerate(zip(all_nodes, coordinates)):
        for j, (node_j, (x_j, y_j)) in enumerate(zip(all_nodes, coordinates)):
            if i != j:
                distance = find_distance(x_i, y_i, x_j, y_j)

                model.add_edge(node_i, node_j, distance=round(distance),
                               duration=round(distance / scenario.vehicle_speed))

    model.add_vehicle_type(num_available=len(scenario.orders), capacity=scenario.vehicle_capacity,
                           shift_duration=scenario.vehicle_shift_size, fixed_cost=scenario.weights.vehicle_salary,
                           unit_distance_cost=scenario.weights.fuel_cost, max_overtime=0)


def calculate_vehicles_routes(result):
    vehicles = []

    for vehicle_id, route in enumerate(result.best.routes(), start=1):
        order_ids = [scenario.orders[i - 1].id for i in route.visits()]
        times = compute_times(order_ids, scenario)

        vehicles.append({
            "id": vehicle_id,
            "route": [0] + order_ids + [0],
            "time": times,
            "time2": route.duration()
        })

    return vehicles

def create_loaders_task_list(vehicles, scenario):
    data = {
        "routes": []
    }
    for i in vehicles:
        id = i["id"]
        data["routes"].append({
            "id": id,
            "points": [],
            "car_extra_time": scenario.vehicle_shift_size - i["time2"],
        })
        for j in range(1, len(i["time"]) + 1):
            order_data = scenario.orders[i["route"][j] - 1]
            if order_data.loader_cnt == 0:
                continue
            data["routes"][id - 1]["points"].append({
                "id": order_data.id,
                "x": order_data.x,
                "y": order_data.y,
                "loader_cnt": order_data.loader_cnt,
                "loader_service_time": order_data.loader_service_time,
                "vehicle_time": i["time"][j - 1],
                "end_time": order_data.time_window[1]
            })

    filtered_routes = [r for r in data["routes"] if len(r["points"]) > 0]
    for new_id, route in enumerate(filtered_routes, start=1):
        route["id"] = new_id

    data["routes"] = filtered_routes

    with open('loaders_task_list.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    scenario = parse("input.json")
    model = Model()

    fill_model(scenario, model)

    result = model.solve(stop=MaxRuntime(120))

    vehicles = calculate_vehicles_routes(result)
    create_loaders_task_list(vehicles, scenario)
    print(vehicles)
    solve_loaders()