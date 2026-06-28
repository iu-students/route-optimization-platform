import json
from models import Scenario, Depot, Weights, Order
from ortools.sat.python import cp_model
import random
import time


def parse(path):
    with open(path) as f:
        raw = json.load(f)

    depot = Depot(**raw["depot"])
    weights = Weights(**raw["weights"])
    orders = [Order(**o) for o in raw["orders"]]

    print(f"[parse] {len(orders)} заказов, "
          f"обяз={sum(1 for o in orders if not o.optional)}, "
          f"опц={sum(1 for o in orders if o.optional)}")

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


def find_distance(x1, y1, x2, y2):
    return round(((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5, 2)


# vehicles

def find_best_route(routes, scenario):
    model = cp_model.CpModel()

    x = [model.NewBoolVar(f"route_{r['route_id']}") for r in routes]

    covers = {order.id: [] for order in scenario.orders}

    for i, route in enumerate(routes):
        for oid in route["order_ids"]:
            covers[oid].append(x[i])

    objective = 0
    penalty = scenario.weights.optional_order_penalty

    for order in scenario.orders:
        if order.optional:
            missed = model.NewBoolVar(f"miss_{order.id}")
            model.Add(sum(covers[order.id]) + missed == 1)
            objective += missed * penalty * 100
        else:
            model.Add(sum(covers[order.id]) == 1)

    for i, route in enumerate(routes):
        objective += int(route["cost"] * 100) * x[i]

    model.Minimize(objective)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30

    print(f"[cp-sat/vehicles] решаем: {len(routes)} маршрутов...")
    t0 = time.time()
    status = solver.Solve(model)
    print(f"[cp-sat/vehicles] {solver.StatusName(status)}, "
          f"objective={solver.ObjectiveValue()/100:.2f}, "
          f"{time.time()-t0:.1f}s")

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(
            f"vehicle CP-SAT не нашёл решения: "
            f"status={solver.StatusName(status)}. "
            f"Скорее всего пул не покрывает все обязательные заказы.")

    return solver, x


def build_solution(routes, solver, x):
    solution = {"vehicles": []}
    vehicle_id = 1

    for i, route in enumerate(routes):
        if solver.Value(x[i]) == 1:
            solution["vehicles"].append({
                "vehicle_id": vehicle_id,
                "route": [0] + route["order_ids"] + [0],
                "time": route["arrival_times"],
                "cost": route["cost"],
            })
            vehicle_id += 1

    return solution


def eval_route(order_ids, scenario):
    by_id = {o.id: o for o in scenario.orders}

    first = by_id[order_ids[0]]
    first_leg = find_distance(
        scenario.depot.x, scenario.depot.y, first.x, first.y)
    depart = max(
        0.0,
        first.time_window[0] - first_leg / scenario.vehicle_speed)

    cap = 0
    dist = 0.0
    time = depart
    px, py = scenario.depot.x, scenario.depot.y
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
        px, py = o.x, o.y

    back = find_distance(px, py, scenario.depot.x, scenario.depot.y)
    dist += back
    time += back / scenario.vehicle_speed

    if time - depart > scenario.vehicle_shift_size:
        return None

    cost = dist * scenario.weights.fuel_cost + scenario.weights.vehicle_salary
    return arrival_times, cost


def best_insertion_pos(route, order_id, scenario):
    """Лучшая позиция вставки order_id в route. (pos, res) или None."""
    best = None
    best_cost = float('inf')
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
    """Из tw_early — каждый в дешёвую вставку либо новый маршрут."""
    orders_sorted = sorted(
        scenario.orders,
        key=lambda o: o.time_window[0] + random.uniform(-jitter, jitter)
    )

    routes = []
    for order in orders_sorted:
        best_route_idx = -1
        best_pos = None
        best_extra = float('inf')

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
    """Сэвингс-эвристика: стартуем с одиночек, мерджим по убыванию экономии."""
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
            block = savings[k:k + chunk]
            random.shuffle(block)
            savings[k:k + chunk] = block

    for s, a, b in savings:
        if s <= 0:
            break
        ra, rb = where[a], where[b]
        if ra == rb:
            continue
        route_a, route_b = routes[ra], routes[rb]
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
        pool.append({"order_ids": list(seq),
                     "arrival_times": res[0], "cost": res[1]})

    t0 = time.time()
    for o in scenario.orders:
        add([o.id])
    print(f"[pool/vehicles] одиночки: {len(pool)} ({time.time()-t0:.1f}s)")

    t0 = time.time()
    for r in clarke_wright(scenario, perturb=False):
        add(r)
    for _ in range(num_restarts // 4):
        for r in clarke_wright(scenario, perturb=True):
            add(r)
    print(f"[pool/vehicles] после Clarke-Wright: "
          f"{len(pool)} ({time.time()-t0:.1f}s)")

    t0 = time.time()
    for r in insertion_construct(scenario, jitter=0.0):
        add(r)
    for i in range(num_restarts):
        for r in insertion_construct(scenario, jitter=15.0):
            add(r)
        if (i + 1) % 50 == 0:
            print(f"[pool/vehicles] insertion рестарт "
                  f"{i+1}/{num_restarts}, пул={len(pool)}")
    print(f"[pool/vehicles] итого: {len(pool)} маршрутов "
          f"({time.time()-t0:.1f}s)")

    return pool


def find_vehicles_routes(scenario, num_restarts=200):
    pool = generate_pool(scenario, num_restarts)

    all_pool_routes = []
    for i, route in enumerate(pool):
        all_pool_routes.append({
            "route_id": i + 1,
            "order_ids": route["order_ids"],
            "arrival_times": route["arrival_times"],
            "cost": route["cost"],
        })

    with open("all_possible_vehicles_routes.json", "w") as file:
        json.dump(all_pool_routes, file, indent=4)

    solver, x = find_best_route(all_pool_routes, scenario)

    sol = build_solution(all_pool_routes, solver, x)
    print(f"[vehicles] выбрано машин: {len(sol['vehicles'])}")
    return sol

# Loaders


def build_slots(solution, scenario):
    by_id = {order.id: order for order in scenario.orders}
    slots = []

    for vehicle in solution["vehicles"]:
        order_ids = vehicle["route"][1:-1]
        times = vehicle["time"]

        for order_id, arrival in zip(order_ids, times):
            order = by_id[order_id]

            for k in range(order.loader_cnt):
                slots.append({
                    "slot_id": len(slots),
                    "order_id": order_id,
                    "x": order.x,
                    "y": order.y,
                    "start": arrival,
                    "service": order.loader_service_time,
                })

    return slots


def eval_chain(slot_ids, slots, scenario):
    """Проверка цепочки + расчёт cost. None если нефизибл."""
    if not slot_ids:
        return None

    first = slots[slot_ids[0]]
    home_x, home_y = first["x"], first["y"]

    time = first["start"] + first["service"]

    for i in range(1, len(slot_ids)):
        prev = slots[slot_ids[i - 1]]
        cur = slots[slot_ids[i]]
        d = find_distance(prev["x"], prev["y"], cur["x"], cur["y"])
        time += d / scenario.loader_speed
        if time > cur["start"]:
            return None
        time = cur["start"] + cur["service"]

    last = slots[slot_ids[-1]]
    back = (find_distance(last["x"], last["y"], home_x, home_y)
            / scenario.loader_speed)
    shift = (time + back) - first["start"]

    if shift > scenario.loader_shift_size:
        return None

    return (scenario.weights.loader_salary
            + scenario.weights.loader_work * shift)


def chains_insertion_construct(slots, scenario, jitter=0.0):
    order_by = sorted(
        range(len(slots)),
        key=lambda i: slots[i]["start"] + random.uniform(-jitter, jitter)
    )

    chains = []
    chain_costs = []

    for sid in order_by:
        cur_order = slots[sid]["order_id"]

        best_idx = -1
        best_extra = float('inf')
        best_new_cost = None

        for ci, chain in enumerate(chains):
            if any(slots[s]["order_id"] == cur_order for s in chain):
                continue

            new_cost = eval_chain(chain + [sid], slots, scenario)

            if new_cost is None:
                continue

            extra = new_cost - chain_costs[ci]

            if extra < best_extra:
                best_extra = extra
                best_idx = ci
                best_new_cost = new_cost

        singleton_cost = eval_chain([sid], slots, scenario)
        if singleton_cost is None:
            continue

        if best_idx >= 0 and best_extra < singleton_cost:
            chains[best_idx].append(sid)
            chain_costs[best_idx] = best_new_cost
        else:
            chains.append([sid])
            chain_costs.append(singleton_cost)

    return list(zip(chains, chain_costs))


def generate_loader_pool(slots, scenario, num_restarts=100):
    pool = []
    seen = set()

    def add(chain, cost):
        key = tuple(chain)
        if key in seen:
            return
        seen.add(key)
        pool.append({
            "slot_ids": list(chain),
            "order_ids": [slots[s]["order_id"] for s in chain],
            "cost": cost,
        })

    print(f"[pool/loaders] всего слотов: {len(slots)}")

    t0 = time.time()

    for sid in range(len(slots)):
        c = eval_chain([sid], slots, scenario)
        if c is not None:
            add([sid], c)

    for chain, cost in chains_insertion_construct(slots, scenario, jitter=0.0):
        add(chain, cost)

    for i in range(num_restarts):
        for chain, cost in chains_insertion_construct(
                slots, scenario, jitter=10.0):
            add(chain, cost)

        if (i + 1) % 25 == 0:
            print(f"[pool/loaders] рестарт "
                  f"{i+1}/{num_restarts}, пул={len(pool)}")

    print(f"[pool/loaders] итого: {len(pool)} цепочек ({time.time()-t0:.1f}s)")

    return pool


def find_best_loaders(pool, slots):
    model = cp_model.CpModel()

    y = [model.NewBoolVar(f"chain_{i}") for i in range(len(pool))]

    covers = {s: [] for s in range(len(slots))}
    for i, chain in enumerate(pool):
        for slot_id in chain["slot_ids"]:
            covers[slot_id].append(y[i])

    for slot_id in range(len(slots)):
        model.Add(sum(covers[slot_id]) == 1)

    objective = sum(
        int(chain["cost"] * 100) * y[i]
        for i, chain in enumerate(pool))

    model.Minimize(objective)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30

    print(f"[cp-sat/loaders] решаем: {len(pool)} цепочек...")
    t0 = time.time()
    status = solver.Solve(model)
    print(f"[cp-sat/loaders] {solver.StatusName(status)}, "
          f"objective={solver.ObjectiveValue()/100:.2f}, "
          f"{time.time()-t0:.1f}s")

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(
            f"loader CP-SAT не нашёл решения: "
            f"status={solver.StatusName(status)}. "
            f"Скорее всего пул не покрывает все слоты.")

    return solver, y


def build_loaders(pool, solver, y):
    loaders = []
    loader_id = 1
    for i, chain in enumerate(pool):
        if solver.Value(y[i]) == 1:
            loaders.append({
                "id": loader_id,
                "route": chain["order_ids"],
            })
            loader_id += 1
    return loaders


def find_loaders_routes(solution, scenario, num_restarts=100):
    slots = build_slots(solution, scenario)

    if not slots:
        return []

    pool = generate_loader_pool(slots, scenario, num_restarts)

    with open("all_possible_loaders_routes.json", "w") as f:
        json.dump(pool, f, indent=4)

    solver, y = find_best_loaders(pool, slots)

    loaders = build_loaders(pool, solver, y)
    print(f"[loaders] выбрано грузчиков: {len(loaders)}")

    return loaders


if __name__ == "__main__":
    t_start = time.time()
    filename = 'test_cases/t1.json'
    scenario = parse(filename)

    n = len(scenario.orders)
    if n > 500:
        v_restarts, l_restarts = 50, 30
    elif n > 200:
        v_restarts, l_restarts = 100, 60
    else:
        v_restarts, l_restarts = 200, 100

    print(f"[main] заказов={n} → vehicle_restarts={v_restarts}, "
          f"loader_restarts={l_restarts}")

    solution = find_vehicles_routes(scenario, num_restarts=v_restarts)
    solution["loaders"] = find_loaders_routes(
        solution, scenario, num_restarts=l_restarts)

    with open('test_cases/my_sol_t3.json', "w") as f:
        json.dump(solution, f, indent=4)

    print(f"\n[ИТОГО] {time.time()-t_start:.1f}s, "
          f"машин={len(solution['vehicles'])}, "
          f"грузчиков={len(solution['loaders'])}")
