# flake8: noqa: E501
import json
import random
import time
from ortools.sat.python import cp_model
from common_functions import find_distance


def _try_place_order(oid, routes_dict, exclude_idx, scenario):
    """Ищет лучшую позицию для вставки oid в любой из routes_dict,
    кроме exclude_idx. Возвращает (target_idx, pos) или None."""
    best_target = None
    best_extra = float("inf")
    best_pos = None
    for ti, troute in routes_dict.items():
        if ti == exclude_idx:
            continue
        ins = best_insertion_pos(troute, oid, scenario)
        if ins is None:
            continue
        pos, res = ins
        if res[1] < best_extra:
            best_extra = res[1]
            best_target = ti
            best_pos = pos
    if best_target is None:
        return None
    return (best_target, best_pos)


def _try_swap_rescue(oid, routes_dict, source_idx, scenario):
    """Заказ oid некуда вставить напрямую. Пробуем: вытеснить один заказ
    из какого-то целевого маршрута, поставить oid на его место, а
    вытесненный заказ пристроить в третий маршрут (или туда же, где
    получится). Возвращает обновлённый routes_dict (копию) или None,
    если ни один обмен не сработал."""
    for ti, troute in list(routes_dict.items()):
        if ti == source_idx:
            continue
        for k, evict_oid in enumerate(troute):
            reduced = troute[:k] + troute[k + 1:]
            ins = best_insertion_pos(reduced, oid, scenario)
            if ins is None:
                continue
            pos, _ = ins
            candidate_troute = reduced[:pos] + [oid] + reduced[pos:]

            trial = dict(routes_dict)
            trial[ti] = candidate_troute
            placed = _try_place_order(evict_oid, trial, ti, scenario)
            if placed is None:
                continue
            ei, epos = placed
            r = trial[ei]
            trial[ei] = r[:epos] + [evict_oid] + r[epos:]
            return trial
    return None


def consolidate_routes(solution, scenario, deadline=None):
    """Пост-обработка: пытается полностью опустошить наименее загруженные
    (по объёму) машины. Сначала пробует прямую вставку каждого заказа
    в другой маршрут (best_insertion_pos). Если прямая вставка невозможна -
    пробует swap-эвакуацию (_try_swap_rescue): вытеснить кого-то из целевого
    маршрута, освободив место, и пристроить вытесненного в третий маршрут.
    Если ВСЕ заказы машины удаётся переселить - машина убирается целиком
    (экономия vehicle_salary). Использует уже существующие
    best_insertion_pos/eval_route, не меняет генерацию пула и не трогает
    CP-SAT. Вызывать ДО построения маршрутов грузчиков (build_slots
    зависит от финальных маршрутов машин).

    deadline - абсолютный time.time()-timestamp. У этой функции нет
    встроенного лимита по умолчанию, а её сложность растёт нелинейно с
    числом машин (swap-эвакуация перебирает пары маршрутов) - на больших
    инстансах без дедлайна она может занять непредсказуемо много времени."""
    routes = [
        [pid for pid in v["route"] if pid != 0] for v in solution["vehicles"]
    ]
    by_id = {o.id: o for o in scenario.orders}

    def route_volume(route):
        return sum(by_id[oid].volume for oid in route)

    order_indices = sorted(
        range(len(routes)), key=lambda i: route_volume(routes[i])
    )

    eliminated = set()
    swap_rescues_used = 0
    timed_out = False
    for idx in order_indices:
        if deadline is not None and time.time() >= deadline:
            timed_out = True
            break
        if idx in eliminated or not routes[idx]:
            continue
        orders_to_move = list(routes[idx])
        target_snapshot = {
            i: list(routes[i])
            for i in range(len(routes))
            if i != idx and i not in eliminated
        }
        success = True
        for oid in orders_to_move:
            placed = _try_place_order(oid, target_snapshot, idx, scenario)
            if placed is not None:
                ti, pos = placed
                r = target_snapshot[ti]
                target_snapshot[ti] = r[:pos] + [oid] + r[pos:]
                continue

            rescued = _try_swap_rescue(oid, target_snapshot, idx, scenario)
            if rescued is not None:
                target_snapshot = rescued
                swap_rescues_used += 1
                continue

            success = False
            break

        if success:
            for ti, r in target_snapshot.items():
                routes[ti] = r
            routes[idx] = []
            eliminated.add(idx)

    new_vehicles = []
    for route in routes:
        if not route:
            continue
        arrival_times, cost, dist = eval_route(route, scenario)
        new_vehicles.append(
            {
                "id": len(new_vehicles) + 1,
                "route": [0] + route + [0],
                "time": arrival_times,
                "cost": round(cost, 2),
                "dist": round(dist, 2),
            }
        )

    timeout_note = " (ДЕДЛАЙН ДОСТИГНУТ, прервано досрочно)" if timed_out else ""
    print(
        f"[consolidate] машин: {len(solution['vehicles'])} → {len(new_vehicles)} "
        f"(устранено: {len(eliminated)}, swap-эвакуаций: {swap_rescues_used}){timeout_note}"
    )
    return {"vehicles": new_vehicles}


def eval_route_with_start(order_ids, scenario, forced_start):
    """Как eval_route, но старт машины из депо задан явно (forced_start),
    а не вычисляется как наиболее ранний возможный. Нужен для проверки
    второго+ рейса той же машины, который не может стартовать раньше,
    чем машина вернётся в депо после предыдущего рейса + load_time.
    Возвращает (arrival_times, dist, return_time) или None, если
    time window/capacity нарушены. НЕ проверяет vehicle_shift_size -
    это делает вызывающий код на уровне всей цепочки рейсов."""
    by_id = {o.id: o for o in scenario.orders}
    cap = 0
    dist = 0.0
    time = forced_start
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
    return (arrival_times, dist, time)


def merge_multi_trip_routes(solution, scenario, deadline=None):
    """Пост-обработка (после consolidate_routes): жадно объединяет уже
    выбранные отдельные маршруты (каждый - 1 машина) в multi-trip машины
    там, где остаток смены позволяет выполнить ещё один рейс после
    возврата в депо + depot.load_time. Не меняет генерацию пула и не
    трогает CP-SAT.

    Экономит vehicle_salary за каждую объединённую пару (лишняя машина
    не нужна), платит только depot.load_time за второй+ рейс. Топливо
    не меняется - оба рейса и так идут через депо.

    ПРИМЕЧАНИЕ: на реальных инстансах (i3, i4) эмпирически НЕ нашлось
    ни одной валидной пары - распределение заказов по времени суток
    шире, чем vehicle_shift_size, поэтому ни один рейс не успевает
    вернуться и начать второй в пределах смены. Логика верна и
    протестирована (не даёт false positives), но её реальный эффект
    зависит от конкретного инстанса - на некоторых входных данных
    может не сработать вообще, и это нормально, не баг."""
    by_id = {o.id: o for o in scenario.orders}
    load_time = scenario.depot.load_time

    trips = []
    for v in solution["vehicles"]:
        order_ids = [pid for pid in v["route"] if pid != 0]
        first = by_id[order_ids[0]]
        first_leg = find_distance(
            scenario.depot.x, scenario.depot.y, first.x, first.y
        )
        natural_depart = max(
            0.0, first.time_window[0] - first_leg / scenario.vehicle_speed
        )
        res = eval_route_with_start(order_ids, scenario, natural_depart)
        if res is None:
            trips.append(
                {
                    "order_ids": order_ids,
                    "depart": natural_depart,
                    "return_time": None,
                    "arrival_times": v["time"],
                    "dist": v["dist"],
                }
            )
            continue
        arrival_times, dist, return_time = res
        trips.append(
            {
                "order_ids": order_ids,
                "depart": natural_depart,
                "return_time": return_time,
                "arrival_times": arrival_times,
                "dist": dist,
            }
        )

    trips.sort(key=lambda t: t["depart"])

    vehicles_merged = []
    used = [False] * len(trips)

    for i, trip in enumerate(trips):
        if deadline is not None and time.time() >= deadline:
            # если время вышло - оставшиеся рейсы переносим как есть,
            # без попытки объединения
            for j, t2 in enumerate(trips):
                if not used[j]:
                    used[j] = True
                    vehicles_merged.append(
                        {
                            "id": len(vehicles_merged) + 1,
                            "route": [0] + t2["order_ids"] + [0],
                            "time": t2["arrival_times"],
                            "dist": round(t2["dist"], 2),
                            "cost": round(
                                t2["dist"] * scenario.weights.fuel_cost
                                + scenario.weights.vehicle_salary, 2,
                            ),
                            "trips": 1,
                        }
                    )
            break
        if used[i]:
            continue
        used[i] = True
        vehicle_trips = [trip]
        shift_start = trip["depart"]
        last_return = trip["return_time"]

        progress = True
        while progress and last_return is not None:
            progress = False
            threshold = last_return + load_time
            best_j = None
            best_extra_delay = float("inf")
            for j, cand in enumerate(trips):
                if used[j]:
                    continue
                extra_delay = max(0.0, threshold - cand["depart"])
                forced_start = max(cand["depart"], threshold)
                res = eval_route_with_start(
                    cand["order_ids"], scenario, forced_start
                )
                if res is None:
                    continue
                _, _, return_time2 = res
                if return_time2 - shift_start > scenario.vehicle_shift_size:
                    continue
                if extra_delay < best_extra_delay:
                    best_extra_delay = extra_delay
                    best_j = (j, res)
            if best_j is not None:
                j, res = best_j
                arrival_times2, dist2, return_time2 = res
                used[j] = True
                vehicle_trips.append(
                    {
                        "order_ids": trips[j]["order_ids"],
                        "arrival_times": arrival_times2,
                        "dist": dist2,
                        "reload_start": max(trips[j]["depart"], threshold),
                    }
                )
                last_return = return_time2
                progress = True

        route = [0]
        all_times = []
        all_dist = 0.0
        for idx, t in enumerate(vehicle_trips):
            if idx > 0:
                # единственный разделительный "0" между рейсами (возврат
                # в депо = начало загрузки следующего рейса, это ОДНА
                # точка, а не два отдельных события) + соответствующая
                # метка времени начала загрузки (см. PDF: "time - времена
                # начала разгрузки на заказах и начала загрузки в депо,
                # если ТС делает несколько кругов")
                route.append(0)
                all_times.append(round(t["reload_start"], 2))
            route.extend(t["order_ids"])
            all_times.extend(t["arrival_times"])
            all_dist += t["dist"]
        route.append(0)

        vehicles_merged.append(
            {
                "id": len(vehicles_merged) + 1,
                "route": route,
                "time": all_times,
                "dist": round(all_dist, 2),
                "cost": round(
                    all_dist * scenario.weights.fuel_cost
                    + scenario.weights.vehicle_salary,
                    2,
                ),
                "trips": len(vehicle_trips),
            }
        )

    multi_count = sum(1 for v in vehicles_merged if v["trips"] > 1)
    print(
        f"[multi-trip] машин: {len(solution['vehicles'])} → {len(vehicles_merged)} "
        f"(из них multi-trip: {multi_count})"
    )
    return {"vehicles": vehicles_merged}


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

    # Тот же защитный retry, что и в find_best_loaders - если урезанный
    # дедлайном time_limit слишком мал для нахождения хоть какого-то
    # допустимого решения (status=UNKNOWN), не падаем сразу.
    attempt_time_limit = max(time_limit, 1)
    status = None
    for attempt in range(4):
        solver.parameters.max_time_in_seconds = attempt_time_limit
        print(
            f"[cp-sat/vehicles] решаем: {len(routes)} маршрутов "
            f"(лимит={attempt_time_limit}s, попытка {attempt + 1})..."
        )
        t0 = time.time()
        status = solver.Solve(model)
        print(
            f"[cp-sat/vehicles] {solver.StatusName(status)}, objective={solver.ObjectiveValue() / 100:.2f}, {time.time() - t0:.1f}s"
        )
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return (solver, x, missed_vars)
        attempt_time_limit *= 5
        print(
            f"[cp-sat/vehicles] status={solver.StatusName(status)}, "
            f"не нашли допустимого решения - пробуем с бОльшим лимитом"
        )

    raise RuntimeError(
        f"vehicle CP-SAT не нашёл решения даже после нескольких попыток: "
        f"status={solver.StatusName(status)}. Скорее всего пул не покрывает все обязательные заказы."
    )


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


def eval_route(order_ids, scenario, by_id=None):
    if by_id is None:
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


def best_insertion_pos(route, order_id, scenario, by_id=None):
    if by_id is None:
        by_id = {o.id: o for o in scenario.orders}
    best = None
    best_cost = float("inf")
    for pos in range(len(route) + 1):
        new_seq = route[:pos] + [order_id] + route[pos:]
        res = eval_route(new_seq, scenario, by_id=by_id)
        if res is None:
            continue
        if res[1] < best_cost:
            best_cost = res[1]
            best = (pos, res)
    return best


def insertion_construct(scenario, jitter=0.0, deadline=None, by_id=None):
    if by_id is None:
        by_id = {o.id: o for o in scenario.orders}
    orders_sorted = sorted(
        scenario.orders,
        key=lambda o: o.time_window[0] + random.uniform(-jitter, jitter),
    )
    routes = []
    for order in orders_sorted:
        if deadline is not None and time.time() >= deadline:
            # прерываемся посреди построения - уже собранные маршруты
            # валидны сами по себе, просто не все заказы успели попасть
            # в какой-то маршрут за этот конкретный рестарт
            break
        best_route_idx = -1
        best_pos = None
        best_extra = float("inf")
        for ri, route in enumerate(routes):
            base = eval_route(route, scenario, by_id=by_id)
            if base is None:
                continue
            ins = best_insertion_pos(route, order.id, scenario, by_id=by_id)
            if ins is None:
                continue
            pos, res = ins
            extra = res[1] - base[1]
            if extra < best_extra:
                best_extra = extra
                best_route_idx = ri
                best_pos = pos
        new_route = eval_route([order.id], scenario, by_id=by_id)
        if new_route is None:
            continue
        if best_route_idx >= 0 and best_extra < new_route[1]:
            r = routes[best_route_idx]
            routes[best_route_idx] = r[:best_pos] + [order.id] + r[best_pos:]
        else:
            routes.append([order.id])
    return routes


def clarke_wright(scenario, perturb=False, by_id=None):
    if by_id is None:
        by_id = {o.id: o for o in scenario.orders}
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
        if eval_route(merged, scenario, by_id=by_id) is None:
            continue
        routes[ra] = merged
        routes[rb] = []
        for oid in merged:
            where[oid] = ra
    return [r for r in routes if r]


def generate_pool(scenario, num_restarts=200, deadline=None):
    """deadline - абсолютный time.time()-timestamp, после которого рестарты
    прекращаются досрочно, даже если num_restarts ещё не исчерпан. Без
    этого num_restarts не гарантирует предсказуемое время - на разных
    инстансах одно и то же число рестартов может занимать сильно разное
    время (зависит от числа заказов и геометрии)."""
    pool = []
    seen = set()
    by_id = {o.id: o for o in scenario.orders}

    def add(seq):
        if not seq:
            return
        key = tuple(seq)
        if key in seen:
            return
        res = eval_route(seq, scenario, by_id=by_id)
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

    def out_of_time():
        return deadline is not None and time.time() >= deadline

    t0 = time.time()
    for o in scenario.orders:
        add([o.id])
    print(f"[pool/vehicles] одиночки: {len(pool)} ({time.time() - t0:.1f}s)")
    STALE_LIMIT = 15  # если пул не растёт N рестартов подряд - хватит,
    # дальше крутить бессмысленно (диминишинг ретёрнс)

    t0 = time.time()
    # Clarke-Wright получает СВОЮ долю пул-бюджета (не весь оставшийся
    # deadline) - иначе он может съесть всё время построения пула,
    # не оставив insertion_construct ни секунды. Эмпирически
    # Clarke-Wright быстро выходит на плато (рост пула прекращается
    # уже после первых ~десятков рестартов на некоторых инстансах).
    cw_deadline = None
    if deadline is not None:
        remaining = max(0.0, deadline - time.time())
        cw_deadline = time.time() + remaining * 0.3

    for r in clarke_wright(scenario, perturb=False, by_id=by_id):
        add(r)
    stale_rounds = 0
    last_size = len(pool)
    for _ in range(num_restarts // 4):
        if cw_deadline is not None and time.time() >= cw_deadline:
            print("[pool/vehicles] бюджет Clarke-Wright исчерпан, переходим к insertion_construct")
            break
        for r in clarke_wright(scenario, perturb=True, by_id=by_id):
            add(r)
        if len(pool) == last_size:
            stale_rounds += 1
            if stale_rounds >= STALE_LIMIT:
                print(
                    f"[pool/vehicles] Clarke-Wright не даёт роста {STALE_LIMIT} "
                    f"рестартов подряд, останавливаем досрочно (пул={len(pool)})"
                )
                break
        else:
            stale_rounds = 0
            last_size = len(pool)
    print(f"[pool/vehicles] после Clarke-Wright: {len(pool)} ({time.time() - t0:.1f}s)")
    t0 = time.time()
    for r in insertion_construct(scenario, jitter=0.0, deadline=deadline, by_id=by_id):
        add(r)
    stale_rounds = 0
    last_size = len(pool)
    for i in range(num_restarts):
        if out_of_time():
            print(
                f"[pool/vehicles] дедлайн достигнут на рестарте {i + 1}/{num_restarts}, "
                f"прерываем (пул={len(pool)})"
            )
            break
        for r in insertion_construct(scenario, jitter=15.0, deadline=deadline, by_id=by_id):
            add(r)
        if len(pool) == last_size:
            stale_rounds += 1
            if stale_rounds >= STALE_LIMIT:
                print(
                    f"[pool/vehicles] insertion_construct не даёт роста {STALE_LIMIT} "
                    f"рестартов подряд, останавливаем досрочно (рестарт {i + 1}, пул={len(pool)})"
                )
                break
        else:
            stale_rounds = 0
            last_size = len(pool)
        if (i + 1) % 50 == 0:
            print(
                f"[pool/vehicles] insertion рестарт {i + 1}/{num_restarts}, пул={len(pool)}"
            )
    print(f"[pool/vehicles] итого: {len(pool)} маршрутов ({time.time() - t0:.1f}s)")
    return pool


def select_routes_from_pool(pool, scenario, time_limit=300, deadline=None, reserve_after=0):
    """Тот же выбор маршрутов через CP-SAT, что и find_vehicles_routes,
    но без generate_pool - пул уже построен и передаётся готовым.
    Используется для дешёвой повторной итерации (feedback), где меняется
    только набор доступных заказов, а не сам процесс генерации кандидатов."""
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

    cpsat_time_limit = time_limit
    if deadline is not None:
        cpsat_time_limit = max(5, min(time_limit, deadline - time.time() - reserve_after))

    solver, x, missed_vars = find_best_route(
        all_pool_routes, scenario, time_limit=cpsat_time_limit
    )
    missed_count = sum((solver.Value(v) for v in missed_vars.values()))
    sol = build_solution(all_pool_routes, solver, x)
    print(f"[vehicles/from-pool] выбрано машин: {len(sol['vehicles'])}")
    return (sol, missed_count)


def find_vehicles_routes(scenario, num_restarts=200, time_limit=300, deadline=None,
                          reserve_after=0, pool_deadline=None):
    """pool_deadline - отдельный (обычно более узкий, чем общий deadline)
    дедлайн специально для generate_pool. Позволяет выделить пулу
    маршрутов свою долю общего бюджета времени, не давая ему съесть
    всё время, нужное CP-SAT/consolidate/грузчикам."""
    effective_pool_deadline = pool_deadline if pool_deadline is not None else deadline
    pool = generate_pool(scenario, num_restarts, deadline=effective_pool_deadline)
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

    # Лимит CP-SAT считаем СЕЙЧАС, после того как пул уже построен -
    # если считать его заранее (до generate_pool), он не будет учитывать
    # время, реально потраченное на построение пула, и общий дедлайн
    # можно легко превысить.
    cpsat_time_limit = time_limit
    if deadline is not None:
        cpsat_time_limit = max(5, min(time_limit, deadline - time.time() - reserve_after))

    solver, x, missed_vars = find_best_route(
        all_pool_routes, scenario, time_limit=cpsat_time_limit
    )
    missed_count = sum((solver.Value(v) for v in missed_vars.values()))
    sol = build_solution(all_pool_routes, solver, x)
    print(f"[vehicles] выбрано машин: {len(sol['vehicles'])}")
    return (sol, missed_count, pool)