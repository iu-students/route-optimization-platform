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
        # route: [0, заказы_рейса_1, 0, заказы_рейса_2, 0, ...] — при
        # multi-trip внутри могут быть ДОПОЛНИТЕЛЬНЫЕ "0" (возврат в депо
        # между рейсами). Каждому такому внутреннему "0" соответствует
        # ОДНА запись в times — метка начала загрузки в депо (см. PDF),
        # а не время прибытия на заказ. Наивный route[1:-1]/zip(times)
        # (без учёта внутренних "0") даёт по_id[0] KeyError на
        # multi-trip машинах — 0 не заказ, а депо.
        route = vehicle["route"]
        times = vehicle["time"]
        ti = 0
        for i in range(1, len(route) - 1):
            pid = route[i]
            if pid == 0:
                # служебная метка начала загрузки в депо — пропускаем,
                # она не заказ и грузчиков на ней не бывает
                ti += 1
                continue
            arrival = times[ti]
            ti += 1
            order = by_id[pid]
            for k in range(order.loader_cnt):
                slots.append(
                    {
                        "slot_id": len(slots),
                        "order_id": pid,
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


def generate_loader_pool(slots, scenario, num_restarts=100, deadline=None):
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
    STALE_LIMIT = 15
    stale_rounds = 0
    last_size = len(pool)
    for i in range(num_restarts):
        if deadline is not None and time.time() >= deadline:
            print(f"[pool/loaders] дедлайн достигнут на рестарте {i + 1}/{num_restarts}, прерываем")
            break
        for chain, (cost, shift) in chains_insertion_construct(
            slots, scenario, jitter=10.0
        ):
            add(chain, cost, shift)
        if len(pool) == last_size:
            stale_rounds += 1
            if stale_rounds >= STALE_LIMIT:
                print(
                    f"[pool/loaders] пул не растёт {STALE_LIMIT} рестартов подряд, "
                    f"останавливаем досрочно (рестарт {i + 1}, пул={len(pool)})"
                )
                break
        else:
            stale_rounds = 0
            last_size = len(pool)
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

    # Если урезанный дедлайном time_limit слишком мал, чтобы CP-SAT успел
    # найти ХОТЬ КАКОЕ-ТО допустимое решение (status=UNKNOWN), не падаем
    # сразу — крах пайплайна без единого выходного файла хуже, чем
    # превышение бюджета времени. Даём больше времени по нарастающей.
    attempt_time_limit = max(time_limit, 1)
    status = None
    for attempt in range(4):
        solver.parameters.max_time_in_seconds = attempt_time_limit
        print(
            f"[cp-sat/loaders] решаем: {len(pool)} цепочек "
            f"(лимит={attempt_time_limit}s, попытка {attempt + 1})..."
        )
        t0 = time.time()
        status = solver.Solve(model)
        print(
            f"[cp-sat/loaders] {solver.StatusName(status)}, objective={solver.ObjectiveValue() / 100:.2f}, {time.time() - t0:.1f}s"
        )
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return (solver, y)
        attempt_time_limit *= 5
        print(
            f"[cp-sat/loaders] status={solver.StatusName(status)}, "
            f"не нашли допустимого решения — пробуем с бОльшим лимитом"
        )

    raise RuntimeError(
        f"loader CP-SAT не нашёл решения даже после нескольких попыток: "
        f"status={solver.StatusName(status)}. Скорее всего пул не покрывает все слоты."
    )


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




def find_loaders_routes(solution, scenario, num_restarts=100, time_limit=300, deadline=None,
                         reserve_after=0, pool_deadline=None):
    slots = build_slots(solution, scenario)
    if not slots:
        return []
    effective_pool_deadline = pool_deadline if pool_deadline is not None else deadline
    pool = generate_loader_pool(slots, scenario, num_restarts, deadline=effective_pool_deadline)
    with open("all_possible_loaders_routes.json", "w") as f:
        json.dump(pool, f, indent=4)

    cpsat_time_limit = time_limit
    if deadline is not None:
        cpsat_time_limit = max(2, min(time_limit, deadline - time.time() - reserve_after))

    solver, y = find_best_loaders(pool, slots, time_limit=cpsat_time_limit)
    loaders = build_loaders(pool, solver, y)
    print(f"[loaders] выбрано грузчиков: {len(loaders)}")
    return loaders