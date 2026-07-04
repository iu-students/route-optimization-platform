# flake8: noqa: E501
import json
import random
import time
from ortools.sat.python import cp_model
from common_functions import find_distance


def build_slots(solution, scenario):
    by_id = {order.id: order for order in scenario.orders}
    slots = []
    for vehicle in solution["vehicles"]:
        order_ids = vehicle["route"][1:-1]
        times = vehicle["time"]
        for order_id, arrival in zip(order_ids, times):
            order = by_id[order_id]
            for k in range(order.loader_cnt):
                slots.append(
                    {
                        "slot_id": len(slots),
                        "order_id": order_id,
                        "x": order.x,
                        "y": order.y,
                        "start": arrival,
                        "service": order.loader_service_time,
                    }
                )
    return slots


def eval_chain(slot_ids, slots, scenario):
    if not slot_ids:
        return None
    first = slots[slot_ids[0]]
    home_x, home_y = (first["x"], first["y"])
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
    back = find_distance(last["x"], last["y"], home_x, home_y) / scenario.loader_speed
    shift = time + back - first["start"]
    if shift > scenario.loader_shift_size:
        return None
    cost = scenario.weights.loader_salary + scenario.weights.loader_work * shift
    return (cost, shift)


def chains_insertion_construct(slots, scenario, jitter=0.0):
    order_by = sorted(
        range(len(slots)),
        key=lambda i: slots[i]["start"] + random.uniform(-jitter, jitter),
    )
    chains = []
    chain_costs = []
    for sid in order_by:
        cur_order = slots[sid]["order_id"]
        best_idx = -1
        best_extra = float("inf")
        best_new_cost = None
        for ci, chain in enumerate(chains):
            if any((slots[s]["order_id"] == cur_order for s in chain)):
                continue
            res = eval_chain(chain + [sid], slots, scenario)
            if res is None:
                continue
            new_cost, new_shift = res
            extra = new_cost - chain_costs[ci][0]
            if extra < best_extra:
                best_extra = extra
                best_idx = ci
                best_new_cost = (new_cost, new_shift)
        singleton_res = eval_chain([sid], slots, scenario)
        if singleton_res is None:
            continue
        singleton_cost, singleton_shift = singleton_res
        if best_idx >= 0 and best_extra < singleton_cost:
            chains[best_idx].append(sid)
            chain_costs[best_idx] = best_new_cost
        else:
            chains.append([sid])
            chain_costs.append((singleton_cost, singleton_shift))
    return list(zip(chains, chain_costs))


def generate_loader_pool(slots, scenario, num_restarts=100):
    pool = []
    seen = set()

    def add(chain, cost, shift):
        key = tuple(chain)
        if key in seen:
            return
        seen.add(key)
        pool.append(
            {
                "slot_ids": list(chain),
                "order_ids": [slots[s]["order_id"] for s in chain],
                "cost": cost,
                "shift": shift,
            }
        )

    print(f"[pool/loaders] всего слотов: {len(slots)}")
    t0 = time.time()
    for sid in range(len(slots)):
        res = eval_chain([sid], slots, scenario)
        if res is not None:
            add([sid], res[0], res[1])
    for chain, (cost, shift) in chains_insertion_construct(slots, scenario, jitter=0.0):
        add(chain, cost, shift)
    for i in range(num_restarts):
        for chain, (cost, shift) in chains_insertion_construct(
            slots, scenario, jitter=10.0
        ):
            add(chain, cost, shift)
        if (i + 1) % 25 == 0:
            print(f"[pool/loaders] рестарт {i + 1}/{num_restarts}, пул={len(pool)}")
    print(f"[pool/loaders] итого: {len(pool)} цепочек ({time.time() - t0:.1f}s)")
    return pool


def find_best_loaders(pool, slots, time_limit=300):
    model = cp_model.CpModel()
    y = [model.NewBoolVar(f"chain_{i}") for i in range(len(pool))]
    covers = {s: [] for s in range(len(slots))}
    for i, chain in enumerate(pool):
        for slot_id in chain["slot_ids"]:
            covers[slot_id].append(y[i])
    for slot_id in range(len(slots)):
        model.Add(sum(covers[slot_id]) == 1)
    objective = sum((int(chain["cost"] * 100) * y[i] for i, chain in enumerate(pool)))
    model.Minimize(objective)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    print(f"[cp-sat/loaders] решаем: {len(pool)} цепочек (лимит={time_limit}s)...")
    t0 = time.time()
    status = solver.Solve(model)
    print(
        f"[cp-sat/loaders] {solver.StatusName(status)}, objective={solver.ObjectiveValue() / 100:.2f}, {time.time() - t0:.1f}s"
    )
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(
            f"loader CP-SAT не нашёл решения: status={solver.StatusName(status)}. Скорее всего пул не покрывает все слоты."
        )
    return (solver, y)


def build_loaders(pool, solver, y):
    loaders = []
    loader_id = 1
    for i, chain in enumerate(pool):
        if solver.Value(y[i]) == 1:
            loaders.append(
                {"id": loader_id, "route": chain["order_ids"], "shift": chain["shift"]}
            )
            loader_id += 1
    return loaders




def find_loaders_routes(solution, scenario, num_restarts=100, time_limit=300):
    slots = build_slots(solution, scenario)
    if not slots:
        return []
    pool = generate_loader_pool(slots, scenario, num_restarts)
    with open("all_possible_loaders_routes.json", "w") as f:
        json.dump(pool, f, indent=4)
    solver, y = find_best_loaders(pool, slots, time_limit=time_limit)
    loaders = build_loaders(pool, solver, y)
    print(f"[loaders] выбрано грузчиков: {len(loaders)}")
    return loaders
