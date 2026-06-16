import json
import math
import time as _time

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

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


def build_route_dict(order_ids: list, scenario: Scenario, route_id: int) -> dict:
    """
    Компактное описание маршрута: только id заказов и времена прибытия.
    Полные данные заказов берутся из scenario.orders по id.
    """
    times = compute_times(order_ids, scenario)
    return {
        "route_id": route_id,
        "order_ids": order_ids,
        "arrival_times": times,
        "cost": route_cost(order_ids, scenario),
    }


def route_cost(order_ids: list, scenario: Scenario) -> float:
    """Стоимость одного маршрута: топливо + зарплата машины."""
    if not order_ids:
        return 0.0

    by_id = {order.id: order for order in scenario.orders}
    distance = 0.0

    px, py = scenario.depot.x, scenario.depot.y
    for order_id in order_ids:
        order = by_id[order_id]
        distance += find_distance(px, py, order.x, order.y)
        px, py = order.x, order.y
    distance += find_distance(px, py, scenario.depot.x, scenario.depot.y)

    cost = distance * scenario.weights.fuel_cost + scenario.weights.vehicle_salary
    return round(cost, 2)


def fill_model(scenario, cost_noise=None):
    """cost_noise: dict (i,j) -> множитель ~1.0 для возмущения стоимости рёбер."""
    n = len(scenario.orders)

    total_volume = sum(order.volume for order in scenario.orders)
    by_capacity = -(-total_volume // scenario.vehicle_capacity)
    num_vehicles = min(max(by_capacity * 2 + 5, 30), n)

    points = [(scenario.depot.x, scenario.depot.y)] + [(order.x, order.y) for order in scenario.orders]

    distance_matrix = [[0] * (n + 1) for _ in range(n + 1)]
    time_matrix = [[0] * (n + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                d = find_distance(points[i][0], points[i][1], points[j][0], points[j][1])
                distance_matrix[i][j] = round(d)
                time_matrix[i][j] = math.ceil(d / scenario.vehicle_speed)

    service_times = [0] + [order.vehicle_service_time for order in scenario.orders]

    manager = pywrapcp.RoutingIndexManager(n + 1, num_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        base = distance_matrix[i][j] * scenario.weights.fuel_cost
        if cost_noise is not None:
            base *= cost_noise.get((i, j), 1.0)
        return round(base)

    distance_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(distance_index)

    def time_callback(from_index, to_index):
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        return time_matrix[i][j] + service_times[i]

    time_index = routing.RegisterTransitCallback(time_callback)

    horizon = max(order.time_window[1] for order in scenario.orders) + 100
    routing.AddDimension(time_index, horizon, horizon, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")

    for k, order in enumerate(scenario.orders, start=1):
        index = manager.NodeToIndex(k)
        time_dim.CumulVar(index).SetRange(order.time_window[0], order.time_window[1])

    for v in range(num_vehicles):
        time_dim.SetSpanUpperBoundForVehicle(scenario.vehicle_shift_size, v)

    def demand_callback(from_index):
        i = manager.IndexToNode(from_index)
        if i == 0:
            return 0
        return scenario.orders[i - 1].volume

    demand_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_index, 0,
        [scenario.vehicle_capacity] * num_vehicles,
        True, "Capacity",
    )

    for v in range(num_vehicles):
        routing.SetFixedCostOfVehicle(scenario.weights.vehicle_salary, v)

    for k, order in enumerate(scenario.orders, start=1):
        if order.optional:
            index = manager.NodeToIndex(k)
            routing.AddDisjunction([index], scenario.weights.optional_order_penalty)

    return manager, routing


def extract_routes(manager, routing, solution, scenario):
    """Из одного решения вытаскивает все непустые маршруты."""
    routes = []
    for v in range(routing.vehicles()):
        index = routing.Start(v)
        if routing.IsEnd(solution.Value(routing.NextVar(index))):
            continue

        order_ids = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:
                order_ids.append(scenario.orders[node - 1].id)
            index = solution.Value(routing.NextVar(index))

        if order_ids:
            routes.append(tuple(order_ids))
    return routes


def generate_pool(scenario, n_runs=50, time_per_run=2):
    """Запускает CP-солвер много раз с разными настройками, собирает пул маршрутов."""
    import random

    first_strategies = [
        routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION,
        routing_enums_pb2.FirstSolutionStrategy.BEST_INSERTION,
        routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC,
    ]

    metaheuristics = [
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH,
        routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH,
        routing_enums_pb2.LocalSearchMetaheuristic.SIMULATED_ANNEALING,
        routing_enums_pb2.LocalSearchMetaheuristic.GREEDY_DESCENT,
    ]

    n = len(scenario.orders)
    pool = {}  # tuple(order_ids) -> cost
    t0 = _time.time()

    for run in range(n_runs):
        random.seed(run * 17 + 3)
        # случайные мультипликаторы стоимости рёбер ~ U[0.7, 1.3]
        cost_noise = {
            (i, j): random.uniform(0.7, 1.3)
            for i in range(n + 1) for j in range(n + 1) if i != j
        } if run > 0 else None  # первый прогон — без шума, чтобы получить базовое решение

        manager, routing = fill_model(scenario, cost_noise=cost_noise)

        params = pywrapcp.DefaultRoutingSearchParameters()
        params.first_solution_strategy = first_strategies[run % len(first_strategies)]
        params.local_search_metaheuristic = metaheuristics[(run // len(first_strategies)) % len(metaheuristics)]
        params.time_limit.FromSeconds(time_per_run)

        solution = routing.SolveWithParameters(params)

        if solution is None:
            print(f"run {run + 1}/{n_runs}: нет решения")
            continue

        routes = extract_routes(manager, routing, solution, scenario)
        added = 0
        for r in routes:
            if r not in pool:
                pool[r] = route_cost(list(r), scenario)
                added += 1

        print(f"run {run + 1}/{n_runs}: +{added} new (всего {len(routes)}), "
              f"pool = {len(pool)}, elapsed = {round(_time.time() - t0, 1)}s")

    return pool


if __name__ == "__main__":
    scenario = parse("input.json")
    pool = generate_pool(scenario, n_runs=100, time_per_run=2)

    print(f"\nИтого уникальных маршрутов: {len(pool)}")
    print(f"Минимальная стоимость маршрута: {min(pool.values()):.2f}")
    print(f"Максимальная стоимость маршрута: {max(pool.values()):.2f}")
    print(f"Средний размер маршрута: {sum(len(r) for r in pool) / len(pool):.1f} заказов")

    routes_full = [
        build_route_dict(list(order_ids), scenario, route_id=i + 1)
        for i, order_ids in enumerate(pool.keys())
    ]

    # модель заказа — словарь по id (один раз для всего пула)
    orders_model = {
        order.id: {
            "x": order.x,
            "y": order.y,
            "volume": order.volume,
            "time_window": list(order.time_window),
            "vehicle_service_time": order.vehicle_service_time,
            "loader_cnt": order.loader_cnt,
            "loader_service_time": order.loader_service_time,
            "optional": bool(order.optional),
        }
        for order in scenario.orders
    }

    out = {
        "depot": {"x": scenario.depot.x, "y": scenario.depot.y, "load_time": scenario.depot.load_time},
        "vehicle_speed": scenario.vehicle_speed,
        "vehicle_capacity": scenario.vehicle_capacity,
        "vehicle_shift_size": scenario.vehicle_shift_size,
        "loader_speed": scenario.loader_speed,
        "loader_shift_size": scenario.loader_shift_size,
        "weights": {
            "fuel_cost": scenario.weights.fuel_cost,
            "vehicle_salary": scenario.weights.vehicle_salary,
            "loader_salary": scenario.weights.loader_salary,
            "loader_work": scenario.weights.loader_work,
            "optional_order_penalty": scenario.weights.optional_order_penalty,
        },
        "orders": orders_model,
        "routes": routes_full,
    }

    with open("routes_pool.json", "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("saved -> routes_pool.json")