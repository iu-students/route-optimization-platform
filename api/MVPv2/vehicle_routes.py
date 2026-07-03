import json
import random
import time
from ortools.sat.python import cp_model
from common_functions import find_distance


def find_best_route(routes, scenario, time_limit=300):
    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"route_{r['route_id']}") for r in routes]
    covers = {order.id: [] for order in scenario.orders}
    for i, route in enumerate(routes):
        for oid in route["order_ids"]:
            covers[oid].append(x[i])
    objective = 0
    penalty = scenario.weights.optional_order_penalty
    missed_vars = {}
    for order in scenario.orders:
        if order.optional:
            missed = model.NewBoolVar(f"miss_{order.id}")
            model.Add(sum(covers[order.id]) + missed == 1)
            objective += missed * penalty * 100
            missed_vars[order.id] = missed
        else:
            model.Add(sum(covers[order.id]) == 1)
    for i, route in enumerate(routes):
        objective += int(route["cost"] * 100) * x[i]
    model.Minimize(objective)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    print(f"[cp-sat/vehicles] решаем: {len(routes)} маршрутов (лимит={time_limit}s)...")
    t0 = time.time()
    status = solver.Solve(model)
    print(
        f"[cp-sat/vehicles] {solver.StatusName(status)}, objective={solver.ObjectiveValue() / 100:.2f}, {time.time() - t0:.1f}s"
    )
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(
            f"vehicle CP-SAT не нашёл решения: status={solver.StatusName(status)}. Скорее всего пул не покрывает все обязательные заказы."
        )
    return (solver, x, missed_vars)


def build_solution(routes, solver, x):
    solution = {"vehicles": []}
    vehicle_id = 1
    for i, route in enumerate(routes):
        if solver.Value(x[i]) == 1:
            solution["vehicles"].append(
                {
                    "id": vehicle_id,
                    "route": [0] + route["order_ids"] + [0],
                    "time": route["arrival_times"],
                    "cost": route["cost"],
                    "dist": route["dist"],
                }
            )
            vehicle_id += 1
    return solution


def eval_route(order_ids, scenario):
    by_id = {o.id: o for o in scenario.orders}
    first = by_id[order_ids[0]]
    first_leg = find_distance(scenario.depot.x, scenario.depot.y, first.x, first.y)
    depart = max(0.0, first.time_window[0] - first_leg / scenario.vehicle_speed)
    cap = 0
    dist = 0.0
    time = depart
    px, py = (scenario.depot.x, scenario.depot.y)
    arrival_times = []
    for oid in order_ids:
        o = by_id[oid]
        cap += o.volume
        if cap > scenario.vehicle_capacity:
            return None
        leg = find_distance(px, py, o.x, o.y)
        dist += leg
        time += leg / scenario.vehicle_speed
        if time > o.time_window[1]:
            return None
        time = max(time, o.time_window[0])
        arrival_times.append(round(time, 2))
        time += o.vehicle_service_time
        px, py = (o.x, o.y)
    back = find_distance(px, py, scenario.depot.x, scenario.depot.y)
    dist += back
    time += back / scenario.vehicle_speed
    if time - depart > scenario.vehicle_shift_size:
        return None
    cost = dist * scenario.weights.fuel_cost + scenario.weights.vehicle_salary
    return (arrival_times, cost, dist)


def best_insertion_pos(route, order_id, scenario):
    best = None
    best_cost = float("inf")
    for pos in range(len(route) + 1):
        new_seq = route[:pos] + [order_id] + route[pos:]
        res = eval_route(new_seq, scenario)
        if res is None:
            continue
        if res[1] < best_cost:
            best_cost = res[1]
            best = (pos, res)
    return best


def insertion_construct(scenario, jitter=0.0):
    orders_sorted = sorted(
        scenario.orders,
        key=lambda o: o.time_window[0] + random.uniform(-jitter, jitter),
    )
    routes = []
    for order in orders_sorted:
        best_route_idx = -1
        best_pos = None
        best_extra = float("inf")
        for ri, route in enumerate(routes):
            base = eval_route(route, scenario)
            if base is None:
                continue
            ins = best_insertion_pos(route, order.id, scenario)
            if ins is None:
                continue
            pos, res = ins
            extra = res[1] - base[1]
            if extra < best_extra:
                best_extra = extra
                best_route_idx = ri
                best_pos = pos
        new_route = eval_route([order.id], scenario)
        if new_route is None:
            continue
        if best_route_idx >= 0 and best_extra < new_route[1]:
            r = routes[best_route_idx]
            routes[best_route_idx] = r[:best_pos] + [order.id] + r[best_pos:]
        else:
            routes.append([order.id])
    return routes


def clarke_wright(scenario, perturb=False):
    routes = [[o.id] for o in scenario.orders]
    where = {o.id: i for i, o in enumerate(scenario.orders)}
    depot = scenario.depot
    savings = []
    for i, oi in enumerate(scenario.orders):
        di = find_distance(depot.x, depot.y, oi.x, oi.y)
        for j in range(i + 1, len(scenario.orders)):
            oj = scenario.orders[j]
            dj = find_distance(depot.x, depot.y, oj.x, oj.y)
            dij = find_distance(oi.x, oi.y, oj.x, oj.y)
            savings.append((di + dj - dij, oi.id, oj.id))
    savings.sort(key=lambda t: -t[0])
    if perturb:
        chunk = max(1, len(savings) // 30)
        for k in range(0, len(savings), chunk):
            block = savings[k : k + chunk]
            random.shuffle(block)
            savings[k : k + chunk] = block
    for s, a, b in savings:
        if s <= 0:
            break
        ra, rb = (where[a], where[b])
        if ra == rb:
            continue
        route_a, route_b = (routes[ra], routes[rb])
        if route_a[-1] == a and route_b[0] == b:
            merged = route_a + route_b
        elif route_b[-1] == b and route_a[0] == a:
            merged = route_b + route_a
        else:
            continue
        if eval_route(merged, scenario) is None:
            continue
        routes[ra] = merged
        routes[rb] = []
        for oid in merged:
            where[oid] = ra
    return [r for r in routes if r]


def generate_pool(scenario, num_restarts=200):
    pool = []
    seen = set()

    def add(seq):
        if not seq:
            return
        key = tuple(seq)
        if key in seen:
            return
        res = eval_route(seq, scenario)
        if res is None:
            return
        seen.add(key)
        pool.append(
            {
                "order_ids": list(seq),
                "arrival_times": res[0],
                "cost": res[1],
                "dist": res[2],
            }
        )

    t0 = time.time()
    for o in scenario.orders:
        add([o.id])
    print(f"[pool/vehicles] одиночки: {len(pool)} ({time.time() - t0:.1f}s)")
    t0 = time.time()
    for r in clarke_wright(scenario, perturb=False):
        add(r)
    for _ in range(num_restarts // 4):
        for r in clarke_wright(scenario, perturb=True):
            add(r)
    print(f"[pool/vehicles] после Clarke-Wright: {len(pool)} ({time.time() - t0:.1f}s)")
    t0 = time.time()
    for r in insertion_construct(scenario, jitter=0.0):
        add(r)
    for i in range(num_restarts):
        for r in insertion_construct(scenario, jitter=15.0):
            add(r)
        if (i + 1) % 50 == 0:
            print(
                f"[pool/vehicles] insertion рестарт {i + 1}/{num_restarts}, пул={len(pool)}"
            )
    print(f"[pool/vehicles] итого: {len(pool)} маршрутов ({time.time() - t0:.1f}s)")
    return pool


def find_vehicles_routes(scenario, num_restarts=200, time_limit=300):
    pool = generate_pool(scenario, num_restarts)
    all_pool_routes = []
    for i, route in enumerate(pool):
        all_pool_routes.append(
            {
                "route_id": i + 1,
                "order_ids": route["order_ids"],
                "arrival_times": route["arrival_times"],
                "cost": route["cost"],
                "dist": route["dist"],
            }
        )
    with open("all_possible_vehicles_routes.json", "w") as file:
        json.dump(all_pool_routes, file, indent=4)
    solver, x, missed_vars = find_best_route(
        all_pool_routes, scenario, time_limit=time_limit
    )
    missed_count = sum((solver.Value(v) for v in missed_vars.values()))
    sol = build_solution(all_pool_routes, solver, x)
    print(f"[vehicles] выбрано машин: {len(sol['vehicles'])}")
    return (sol, missed_count)