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
        # финальная 2-opt-полировка: consolidate/swap-эвакуация переставляют
        # заказы по критерию стоимости вставки, из-за чего порядок объезда
        # мог получиться неоптимальным по расстоянию. Набор заказов при этом
        # тот же, так что capacity цела; окна/смену two_opt перепроверяет сам.
        if deadline is None or time.time() < deadline:
            opt = two_opt(route, scenario, by_id=by_id, deadline=deadline)
            if opt is not None:
                route = opt[0]
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


def reduce_vehicles_by_merge(solution, scenario, deadline=None, max_passes=20):
    """Пост-обработка (после consolidate_routes): жадно СЛИВАЕТ пары маршрутов
    в один, убирая целую машину (экономия vehicle_salary). Для каждой пары
    пробует обе конкатенации, прогоняет 2-opt по объединённому маршруту
    (лучший порядок объезда) и принимает слияние ТОЛЬКО если merged-маршрут
    допустим (eval_route: окна H12/H9, смена H2, вместимость H3) И суммарная
    стоимость строго падает. Монотонно: стоимость может лишь уменьшиться,
    поэтому добавление функции не способно ухудшить решение.

    Зачем нужен, если есть consolidate+swap: swap-эвакуация вставляет заказы
    в УЖЕ существующие маршруты с фиксированным расписанием и потому упирается
    в занятые окна (на i4 эмпирически убирает 0 машин). Здесь же расписание
    объединённого маршрута строится С НУЛЯ (eval_route сам выбирает наиболее
    ранний старт) - свободы уложиться в одну смену больше. Особенно полезно при
    низкой загрузке ТС, где машин много из-за ВРЕМЕННОЙ, а не объёмной
    фрагментации: место в кузове есть, мешает только разнос по времени.

    deadline - абсолютный time.time()-timestamp; проверяется между проходами
    и парами. max_passes ограничивает число проходов слияния (каждый проход
    строго уменьшает число машин -> сходимость быстрая)."""
    fuel = scenario.weights.fuel_cost
    salary = scenario.weights.vehicle_salary
    by_id = {o.id: o for o in scenario.orders}
    cap = scenario.vehicle_capacity

    def cost_of(dist):
        return dist * fuel + salary

    routes = [
        [pid for pid in v["route"] if pid != 0] for v in solution["vehicles"]
    ]
    vol = {}  # кэш суммарного объёма маршрута по индексу

    def route_volume(r):
        return sum(by_id[o].volume for o in r)

    merged_total = 0
    passes = 0
    improved = True
    while improved and passes < max_passes:
        if deadline is not None and time.time() >= deadline:
            break
        improved = False
        passes += 1
        i = 0
        while i < len(routes):
            if deadline is not None and time.time() >= deadline:
                break
            if not routes[i]:
                i += 1
                continue
            base_i = eval_route(routes[i], scenario, by_id=by_id)
            vol_i = route_volume(routes[i])
            best_j = None
            best_seq = None
            best_gain = 1e-9  # только строго выгодные слияния
            for j in range(len(routes)):
                if j == i or not routes[j]:
                    continue
                # быстрый отсев по вместимости до дорогих eval/2-opt
                if vol_i + route_volume(routes[j]) > cap:
                    continue
                base_j = eval_route(routes[j], scenario, by_id=by_id)
                if base_j is None:
                    continue
                for concat in (routes[i] + routes[j], routes[j] + routes[i]):
                    res0 = eval_route(concat, scenario, by_id=by_id)
                    if res0 is None:
                        continue
                    seq, res = (concat, res0)
                    opt = two_opt(
                        concat, scenario, by_id=by_id, deadline=deadline
                    )
                    if opt is not None:
                        seq, res = opt
                    # было (две машины) минус стало (одна машина)
                    gain = (cost_of(base_i[2]) + cost_of(base_j[2])) - cost_of(res[2])
                    if gain > best_gain:
                        best_gain = gain
                        best_j = j
                        best_seq = seq
            if best_j is not None:
                routes[i] = best_seq
                routes[best_j] = []
                merged_total += 1
                improved = True
                # НЕ увеличиваем i: вдруг с обновлённым routes[i] сольётся ещё
            else:
                i += 1
        routes = [r for r in routes if r]

    new_vehicles = []
    for route in routes:
        if not route:
            continue
        arrival_times, cost, dist = eval_route(route, scenario, by_id=by_id)
        new_vehicles.append(
            {
                "id": len(new_vehicles) + 1,
                "route": [0] + route + [0],
                "time": arrival_times,
                "cost": round(cost, 2),
                "dist": round(dist, 2),
            }
        )
    print(
        f"[merge] машин: {len(solution['vehicles'])} → {len(new_vehicles)} "
        f"(слияний: {merged_total}, проходов: {passes})"
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


SHIFT_SAFETY_MARGIN = 0.02
# Раньше "защита от границы" была сдвигом depart на SAFETY_MARGIN назад.
# Это НЕ работает для маршрутов, где по всей цепочке заказов нет ни одной
# минуты ожидания (order-ы идут впритык друг за другом без слабины) -
# для них длительность смены МАТЕМАТИЧЕСКИ одна и та же величина при ЛЮБОМ
# depart (см. историю фикса: маршрут [30,149,308,101,245] на i4 даёт
# duration=300.00 РОВНО что при depart=10, что при depart=17.5, что при
# depart=17.52 - сдвиг depart просто переносит весь график целиком, не
# трогая длительность). Единственный работающий способ - явно ОТКЛОНЯТЬ
# маршрут, если его МИНИМАЛЬНО достижимая длительность не имеет запаса
# ниже vehicle_shift_size, а не пытаться "подвинуть" то, что подвинуть
# нельзя.


def _route_floor_duration(order_ids, scenario, by_id):
    """Возвращает (dmax, floor_duration) - depart, дающий минимальную
    длительность смены, и саму эту минимальную длительность (без
    привязки к shift_size - только геометрия/окна). None при нарушении
    capacity или принципиальной недостижимости (окно нарушено при ЛЮБОМ
    depart)."""
    depot = scenario.depot
    speed = scenario.vehicle_speed
    cap = 0
    px, py = (depot.x, depot.y)
    accum = 0.0
    dmax = float("inf")
    for oid in order_ids:
        o = by_id[oid]
        cap += o.volume
        if cap > scenario.vehicle_capacity:
            return None
        leg = find_distance(px, py, o.x, o.y)
        accum += leg / speed
        dmax = min(dmax, o.time_window[1] - accum)
        accum += o.vehicle_service_time
        px, py = (o.x, o.y)
    dmax = max(0.0, dmax)
    # длительность при depart=dmax (минимум по определению dmax)
    time = dmax
    px, py = (depot.x, depot.y)
    for oid in order_ids:
        o = by_id[oid]
        leg = find_distance(px, py, o.x, o.y)
        time += leg / speed
        if time > o.time_window[1] + 1e-9:
            return None
        time = max(time, o.time_window[0])
        time += o.vehicle_service_time
        px, py = (o.x, o.y)
    back = find_distance(px, py, depot.x, depot.y)
    time += back / speed
    return (dmax, time - dmax)


def _best_depart(order_ids, scenario, by_id):
    """Общий O(n) расчёт depart, минимизирующего длительность смены -
    та же формула, что использует _eval_route_mindur (D* =
    max(0, min_i(beta_i - C_i))), вынесенная отдельно, чтобы её мог
    переиспользовать merge_multi_trip_routes (а не только eval_route).
    Возвращает None, если маршрут недопустим ни при каком depart ИЛИ
    если его минимальная длительность не оставляет запаса до
    vehicle_shift_size (см. SHIFT_SAFETY_MARGIN и _route_floor_duration)."""
    res = _route_floor_duration(order_ids, scenario, by_id)
    if res is None:
        return None
    dmax, floor_duration = res
    if floor_duration > scenario.vehicle_shift_size - SHIFT_SAFETY_MARGIN:
        return None
    return dmax


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
        if _SHIFT_MODE == "min_duration":
            # тот же баг, что был в исходном eval_route: наивная формула
            # "выехать точно к открытию окна первого заказа" не
            # минимизирует длительность смены и ложно бракует часть
            # маршрутов. merge_multi_trip_routes раньше считала depart
            # САМА (независимо от eval_route/_SHIFT_MODE) той же наивной
            # формулой - здесь используем корректный _best_depart, если
            # включён режим min_duration, чтобы не откатывать то, что
            # eval_route уже посчитал правильно.
            natural_depart = _best_depart(order_ids, scenario, by_id)
            if natural_depart is None:
                trips.append(
                    {
                        "order_ids": order_ids,
                        "depart": 0.0,
                        "return_time": None,
                        "arrival_times": v["time"],
                        "dist": v["dist"],
                    }
                )
                continue
        else:
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


# --- Режим расчёта смены (H2) ----------------------------------------------
# "min_duration" (ПО УМОЛЧАНИЮ) - выезд ВЫБИРАЕТСЯ так, чтобы
#                  минимизировать длительность смены (spec H2: "отсчёт с
#                  первого выезда", ожидание входит, время выезда не
#                  навязано). И eval_route, и merge_multi_trip_routes
#                  (через общий _best_depart) теперь согласованно
#                  используют эту формулу с одинаковым защитным отступом
#                  от границы vehicle_shift_size - раньше
#                  merge_multi_trip_routes считал depart САМ по старой
#                  наивной формуле и незаметно перезаписывал уже
#                  корректно посчитанные времена, из-за чего готовые
#                  решения реально нарушали H2 (см. историю фикса).
# "earliest"     - СТАРОЕ поведение: выезд фиксируется на самый ранний
#                  (прибыть к открытию окна первого заказа), смена = возврат −
#                  этот ранний выезд. Пессимистично: копит лишнее ожидание
#                  и ложно бракует часть допустимых плотных маршрутов.
#                  Оставлен только для отладки/сравнения (set_shift_mode).
_SHIFT_MODE = "min_duration"


def set_shift_mode(mode):
    """mode: 'earliest' (по умолчанию) | 'min_duration'."""
    global _SHIFT_MODE
    assert mode in ("earliest", "min_duration"), mode
    _SHIFT_MODE = mode


def get_shift_mode():
    return _SHIFT_MODE


def _eval_route_earliest(order_ids, scenario, by_id):
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


def _eval_route_mindur(order_ids, scenario, by_id):
    """Смена = МИНИМАЛЬНАЯ достижимая длительность по времени выезда.

    Ключ: время прибытия к узлу i без ожидания = D + C_i, где C_i -
    накопленное travel+service от выезда. Прибытие в окно требует
    D + C_i <= beta_i, значит максимально поздний (а он и минимизирует
    длительность, т.к. duration(D) невозрастающая) допустимый выезд
    D* = max(0, min_i(beta_i - C_i)). Затем один прямой прогон при D*
    даёт старты, длительность и проверку. Всё за O(n).

    ВАЖНО про границу vehicle_shift_size: D* по построению - это
    максимально допустимый выезд, но НЕЛЬЗЯ "подстраховаться от
    границы", просто отступив на эпсилон от D* назад - если у маршрута
    по всей цепочке заказов нет ни одной минуты ожидания (порядок идёт
    впритык), длительность смены МАТЕМАТИЧЕСКИ одна и та же величина
    при ЛЮБОМ depart (сдвиг depart переносит весь график целиком, не
    меняя разницу return-depart). Для такого маршрута отступить от
    границы попросту НЕКУДА - если его "пол" по длительности равен
    ровно vehicle_shift_size, он останется равен ровно
    vehicle_shift_size при любом выборе depart. Поэтому вместо сдвига
    depart здесь и в _best_depart используется прямое отклонение:
    если минимальная достижимая длительность не оставляет запаса
    SHIFT_SAFETY_MARGIN до vehicle_shift_size - маршрут считается
    недопустимым целиком (см. _route_floor_duration)."""
    res = _route_floor_duration(order_ids, scenario, by_id)
    if res is None:
        return None
    dmax, floor_duration = res
    if floor_duration > scenario.vehicle_shift_size - SHIFT_SAFETY_MARGIN:
        return None

    depot = scenario.depot
    speed = scenario.vehicle_speed
    legs = []
    px, py = (depot.x, depot.y)
    dist = 0.0
    for oid in order_ids:
        o = by_id[oid]
        leg = find_distance(px, py, o.x, o.y)
        legs.append(leg)
        dist += leg
        px, py = (o.x, o.y)
    back = find_distance(px, py, depot.x, depot.y)
    dist += back

    time = dmax
    px, py = (depot.x, depot.y)
    arrival_times = []
    for k, oid in enumerate(order_ids):
        o = by_id[oid]
        time += legs[k] / speed
        if time > o.time_window[1] + 1e-9:
            return None
        time = max(time, o.time_window[0])
        arrival_times.append(round(time, 2))
        time += o.vehicle_service_time
        px, py = (o.x, o.y)
    time += back / speed
    if time - dmax > scenario.vehicle_shift_size + 1e-9:
        return None
    cost = dist * scenario.weights.fuel_cost + scenario.weights.vehicle_salary
    return (arrival_times, cost, dist)


def eval_route(order_ids, scenario, by_id=None):
    if by_id is None:
        by_id = {o.id: o for o in scenario.orders}
    if _SHIFT_MODE == "min_duration":
        return _eval_route_mindur(order_ids, scenario, by_id)
    return _eval_route_earliest(order_ids, scenario, by_id)


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


def two_opt(order_ids, scenario, by_id=None, deadline=None, max_passes=30):
    """Локальная 2-opt оптимизация ПОРЯДКА объезда внутри ОДНОГО маршрута.

    Набор заказов не меняется -> суммарный объём тот же -> H3 (capacity)
    инвариантна и не требует перепроверки. Меняется только последователь-
    ность посещения, поэтому окна (H9/H12) и длительность смены (H2)
    перепроверяем полноценным eval_route на каждом принимаемом ходе.

    Ход принимается ТОЛЬКО если он одновременно (а) сокращает расстояние и
    (б) оставляет маршрут допустимым. Отсюда ключевое свойство: результат
    НЕ ХУЖЕ входа ни по расстоянию, ни по допустимости — значит добавление
    2-opt не может ухудшить ни одно решение / ни один тест, только срезать
    топливо там, где порядок объезда был неоптимален.

    Стоимость: дельта расстояния для разворота сегмента считается за O(1)
    (на симметричной евклидовой метрике при 2-opt меняются ровно два ребра),
    поэтому проход — это ~O(n^2) дешёвых арифметических проверок, а дорогой
    eval_route (O(n)) вызывается лишь ОДИН раз за проход — для лучшего
    найденного хода. Проходов не больше max_passes, а каждый проход строго
    уменьшает расстояние -> сходимость быстрая. deadline прерывает
    оптимизацию между проходами.

    Возвращает (improved_order_ids, res) либо None, если улучшить не удалось
    (в т.ч. если вход короче 4 заказов — на 2-3 точках 2-opt бессмысленен)."""
    if by_id is None:
        by_id = {o.id: o for o in scenario.orders}
    n = len(order_ids)
    if n < 4:
        return None
    base = eval_route(order_ids, scenario, by_id=by_id)
    if base is None:
        return None

    dx, dy = (scenario.depot.x, scenario.depot.y)
    best_seq = list(order_ids)
    best_res = base
    best_dist = base[2]
    improved = False

    for _ in range(max_passes):
        if deadline is not None and time.time() >= deadline:
            break
        # координаты узлов маршрута: pts[0] и pts[n+1] — депо, pts[k] (1..n)
        # — заказ best_seq[k-1]. Дельта разворота сегмента заказов
        # best_seq[i..j-1] затрагивает ровно рёбра (i,i+1) и (j,j+1).
        pts = [(dx, dy)]
        for oid in best_seq:
            o = by_id[oid]
            pts.append((o.x, o.y))
        pts.append((dx, dy))

        best_move = None
        best_delta = -1e-9  # берём только строго улучшающие ходы
        for i in range(n):
            ax, ay = pts[i]
            bx, by_ = pts[i + 1]
            for j in range(i + 2, n + 1):
                cx, cy = pts[j]
                ex, ey = pts[j + 1]
                delta = (
                    find_distance(ax, ay, cx, cy)
                    + find_distance(bx, by_, ex, ey)
                    - find_distance(ax, ay, bx, by_)
                    - find_distance(cx, cy, ex, ey)
                )
                if delta < best_delta:
                    best_delta = delta
                    best_move = (i, j)
        if best_move is None:
            break

        i, j = best_move
        cand = best_seq[:i] + best_seq[i:j][::-1] + best_seq[j:]
        res = eval_route(cand, scenario, by_id=by_id)
        # геометрически ход короче, но окна/смена могут это запретить —
        # тогда просто останавливаемся (лучший ход недопустим). Проверка
        # res[2] < best_dist страхует от расхождений из-за округления.
        if res is None or res[2] >= best_dist - 1e-9:
            break
        best_seq, best_res, best_dist = (cand, res, res[2])
        improved = True

    if not improved:
        return None
    return (best_seq, best_res)


def inter_route_local_search(solution, scenario, deadline=None, max_passes=8):
    """Межмаршрутный локальный поиск (relocate / or-opt-1): перенос ОДНОГО
    заказа из маршрута A в лучшую позицию другого маршрута B, если это
    строго уменьшает суммарную стоимость (топливо + vehicle_salary за
    опустевшие машины).

    Зачем: consolidate_routes убирает машины, two_opt полирует порядок
    ВНУТРИ одного маршрута, но ни один этап не двигает заказы МЕЖДУ
    маршрутами ради чистого снижения дистанции. Разбор разрыва с baseline
    на i4 показал, что крупнейший компонент отставания - именно
    VehicleFuelCost, при уже выигранных грузчиках; relocate закрывает
    ровно эту дыру.

    Монотонная безопасность: ход применяется ТОЛЬКО если (а) оба новых
    маршрута валидны по eval_route (окна, смена, capacity) и (б) суммарная
    стоимость строго падает (с бонусом vehicle_salary, если маршрут-донор
    опустел). Значит результат не хуже входа ни по допустимости, ни по
    стоимости. После завершения ходов изменённые маршруты дополнительно
    полируются two_opt (тоже монотонно безопасным)."""
    by_id = {o.id: o for o in scenario.orders}
    w = scenario.weights

    routes = []
    for v in solution["vehicles"]:
        oids = [pid for pid in v["route"] if pid != 0]
        if oids:
            routes.append(oids)

    def rdist(oids):
        if not oids:
            return 0.0
        res = eval_route(oids, scenario, by_id=by_id)
        return None if res is None else res[2]

    dists = []
    valid = True
    for r in routes:
        d = rdist(r)
        if d is None:
            valid = False
            break
        dists.append(d)
    if not valid:
        # входное решение почему-то не проходит eval_route - не рискуем,
        # возвращаем как есть
        print("[relocate] вход не прошёл eval_route, пропускаем этап")
        return solution

    n_before = len(routes)
    total_moves = 0
    total_swaps = 0
    passes = 0
    improved = True
    while improved and passes < max_passes:
        if deadline is not None and time.time() >= deadline:
            break
        improved = False
        passes += 1
        for i in range(len(routes)):
            if deadline is not None and time.time() >= deadline:
                break
            if not routes[i]:
                continue
            for oid in list(routes[i]):
                new_i = [x for x in routes[i] if x != oid]
                di_new = rdist(new_i)
                if di_new is None:
                    continue
                base_gain = (dists[i] - di_new) * w.fuel_cost
                if not new_i:
                    base_gain += w.vehicle_salary
                best = None  # (delta, j, new_route_j, dj_new)
                for j in range(len(routes)):
                    if j == i or not routes[j]:
                        continue
                    for pos in range(len(routes[j]) + 1):
                        cand = routes[j][:pos] + [oid] + routes[j][pos:]
                        res = eval_route(cand, scenario, by_id=by_id)
                        if res is None:
                            continue
                        dj_new = res[2]
                        delta = base_gain - (dj_new - dists[j]) * w.fuel_cost
                        if delta > 1e-6 and (best is None or delta > best[0]):
                            best = (delta, j, cand, dj_new)
                if best is not None:
                    _, j, cand, dj_new = best
                    routes[j] = cand
                    dists[j] = dj_new
                    routes[i] = new_i
                    dists[i] = di_new
                    total_moves += 1
                    improved = True

        # --- swap-ход: обмен парой заказов между двумя маршрутами --------
        # relocate не может выполнить "рокировку" (перенос в одну сторону
        # блокируется capacity/окнами, пока встречный заказ не уйдёт) -
        # swap делает обе замены атомарно и находит улучшения, недоступные
        # relocate. Принимается только строгое снижение суммарной
        # дистанции при валидности обоих новых маршрутов.
        if deadline is not None and time.time() >= deadline:
            break
        for i in range(len(routes)):
            if deadline is not None and time.time() >= deadline:
                break
            if not routes[i]:
                continue
            for j in range(i + 1, len(routes)):
                if not routes[j]:
                    continue
                done_pair = False
                for a in list(routes[i]):
                    if done_pair:
                        break
                    base_i_wo = [x for x in routes[i] if x != a]
                    for b in list(routes[j]):
                        base_j_wo = [x for x in routes[j] if x != b]
                        # лучшая позиция b в i-без-a
                        best_i = None
                        for pos in range(len(base_i_wo) + 1):
                            cand = base_i_wo[:pos] + [b] + base_i_wo[pos:]
                            res = eval_route(cand, scenario, by_id=by_id)
                            if res is None:
                                continue
                            if best_i is None or res[2] < best_i[1]:
                                best_i = (cand, res[2])
                        if best_i is None:
                            continue
                        # лучшая позиция a в j-без-b
                        best_j = None
                        for pos in range(len(base_j_wo) + 1):
                            cand = base_j_wo[:pos] + [a] + base_j_wo[pos:]
                            res = eval_route(cand, scenario, by_id=by_id)
                            if res is None:
                                continue
                            if best_j is None or res[2] < best_j[1]:
                                best_j = (cand, res[2])
                        if best_j is None:
                            continue
                        delta = (
                            (dists[i] - best_i[1]) + (dists[j] - best_j[1])
                        ) * w.fuel_cost
                        if delta > 1e-6:
                            routes[i], dists[i] = best_i
                            routes[j], dists[j] = best_j
                            total_swaps += 1
                            improved = True
                            done_pair = True
                            break

    # финальная полировка порядка внутри маршрутов (безопасный two_opt)
    for i in range(len(routes)):
        if deadline is not None and time.time() >= deadline:
            break
        if len(routes[i]) >= 4:
            opt = two_opt(routes[i], scenario, by_id=by_id, deadline=deadline)
            if opt is not None:
                routes[i] = opt[0]

    new_vehicles = []
    vid = 1
    for r in routes:
        if not r:
            continue
        res = eval_route(r, scenario, by_id=by_id)
        if res is None:
            # не должно случаться (все ходы проверялись), но перестрахуемся
            print(f"[relocate] ВНИМАНИЕ: маршрут {r} стал невалидным, откат этапа")
            return solution
        arrival_times, cost, dist = res
        new_vehicles.append(
            {
                "id": vid,
                "route": [0] + r + [0],
                "time": arrival_times,
                "dist": dist,
                "cost": cost,
                "trips": 1,
            }
        )
        vid += 1
    print(
        f"[relocate] ходов: {total_moves}, swap'ов: {total_swaps}, "
        f"машин: {n_before} → {len(new_vehicles)} ({passes} проходов)"
    )
    out = dict(solution)
    out["vehicles"] = new_vehicles
    return out


def perturb_solution(solution, scenario, k=3):
    """Возмущение решения для LNS: k СЛУЧАЙНЫХ допустимых relocate-ходов
    БЕЗ требования улучшения. Нужно, чтобы вырваться из локального
    оптимума, в котором детерминированный локальный поиск застрял:
    после perturbation запускается обычный inter_route_local_search, и
    результат принимается только если ПОЛНАЯ метрика стала лучше
    (контроль на стороне вызывающего кода). Все ходы проверяются на
    допустимость через eval_route, так что возмущённое решение всегда
    валидно."""
    by_id = {o.id: o for o in scenario.orders}
    routes = []
    for v in solution["vehicles"]:
        oids = [pid for pid in v["route"] if pid != 0]
        if oids:
            routes.append(oids)
    if len(routes) < 2:
        return solution

    moves_done = 0
    attempts = 0
    while moves_done < k and attempts < k * 15:
        attempts += 1
        i = random.randrange(len(routes))
        if not routes[i]:
            continue
        j = random.randrange(len(routes))
        if j == i:
            continue
        oid = random.choice(routes[i])
        new_i = [x for x in routes[i] if x != oid]
        if new_i and eval_route(new_i, scenario, by_id=by_id) is None:
            continue
        pos = random.randrange(len(routes[j]) + 1)
        cand = routes[j][:pos] + [oid] + routes[j][pos:]
        if eval_route(cand, scenario, by_id=by_id) is None:
            continue
        routes[i] = new_i
        routes[j] = cand
        moves_done += 1

    new_vehicles = []
    vid = 1
    for r in routes:
        if not r:
            continue
        res = eval_route(r, scenario, by_id=by_id)
        if res is None:
            return solution  # перестраховка: не отдаём невалидное
        arrival_times, cost, dist = res
        new_vehicles.append(
            {
                "id": vid,
                "route": [0] + r + [0],
                "time": arrival_times,
                "dist": dist,
                "cost": cost,
                "trips": 1,
            }
        )
        vid += 1
    out = dict(solution)
    out["vehicles"] = new_vehicles
    return out


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


def ortools_generate_routes(scenario, time_budget=150, num_vehicles=None,
                            first_solution="AUTOMATIC",
                            deadline=None, by_id=None):
    """Генерирует ПЛОТНЫЕ маршруты ТС полноценным CVRPTW-солвером OR-Tools
    Routing (constraint_solver, Guided Local Search) и возвращает список
    последовательностей order_id. Кодирует ровно нашу модель:
      transit по времени = vehicle_service_time(i) + dist(i,j)/vehicle_speed
      (ожидание разрешено slack'ом -> cumul узла = начало обслуживания);
      окно [a,b] на cumul; span time-dim на машину <= vehicle_shift_size;
      capacity-dimension = vehicle_capacity; optional -> AddDisjunction со
      штрафом optional_order_penalty; стоимость дуги = dist*fuel_cost,
      fixed cost машины = vehicle_salary => решатель сам давит ЧИСЛО машин.

    OR-Tools свободно выбирает время выезда (минимизирует простой), поэтому
    его плотные маршруты допустимы ТОЛЬКО в режиме смены 'min_duration';
    вызывающая сторона (generate_pool.add -> eval_route) их провалидирует."""
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2

    orders = scenario.orders
    n = len(orders)
    if n == 0:
        return []
    depot = scenario.depot
    speed = scenario.vehicle_speed
    w = scenario.weights
    if by_id is None:
        by_id = {o.id: o for o in orders}
    if num_vehicles is None:
        num_vehicles = min(n, 100)
    if deadline is not None:
        time_budget = max(1, min(time_budget, deadline - time.time() - 2))

    xs = [depot.x] + [o.x for o in orders]
    ys = [depot.y] + [o.y for o in orders]
    service = [0] + [o.vehicle_service_time for o in orders]
    demand = [0] + [o.volume for o in orders]
    tw = [(0, 0)] + [tuple(o.time_window) for o in orders]
    node_oid = [None] + [o.id for o in orders]

    TIME_SCALE = 100
    COST_SCALE = 100
    horizon = int((max(b for _, b in tw[1:]) + 1) * TIME_SCALE)

    manager = pywrapcp.RoutingIndexManager(n + 1, num_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)

    def dist_ij(i, j):
        return find_distance(xs[i], ys[i], xs[j], ys[j])

    def cost_cb(fi, ti):
        i, j = manager.IndexToNode(fi), manager.IndexToNode(ti)
        return int(round(dist_ij(i, j) * w.fuel_cost * COST_SCALE))

    cost_idx = routing.RegisterTransitCallback(cost_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(cost_idx)
    routing.SetFixedCostOfAllVehicles(int(round(w.vehicle_salary * COST_SCALE)))

    def time_cb(fi, ti):
        i, j = manager.IndexToNode(fi), manager.IndexToNode(ti)
        return int(round((service[i] + dist_ij(i, j) / speed) * TIME_SCALE))

    time_idx = routing.RegisterTransitCallback(time_cb)
    routing.AddDimension(time_idx, horizon, horizon, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")
    for node in range(1, n + 1):
        idx = manager.NodeToIndex(node)
        a, b = tw[node]
        time_dim.CumulVar(idx).SetRange(int(round(a * TIME_SCALE)), int(round(b * TIME_SCALE)))
    shift_scaled = int(round(scenario.vehicle_shift_size * TIME_SCALE))
    for v in range(num_vehicles):
        time_dim.CumulVar(routing.Start(v)).SetRange(0, horizon)
        time_dim.SetSpanUpperBoundForVehicle(shift_scaled, v)

    def demand_cb(fi):
        return demand[manager.IndexToNode(fi)]

    dem_idx = routing.RegisterUnaryTransitCallback(demand_cb)
    routing.AddDimensionWithVehicleCapacity(
        dem_idx, 0, [scenario.vehicle_capacity] * num_vehicles, True, "Cap"
    )

    opt_pen = int(round(w.optional_order_penalty * COST_SCALE))
    # Делаем droppable КАЖДЫЙ узел (не только optional). Иначе, если
    # first-solution эвристика не может разместить хоть один ОБЯЗАТЕЛЬНЫЙ
    # заказ (тугие окна), она проваливается целиком и SolveWithParameters
    # возвращает None -> 0 маршрутов (ровно это наблюдалось на реальном i4).
    # С disjunction на всех узлах решатель всегда достраивает решение, при
    # необходимости выбрасывая неразмещаемый заказ за штраф. Обязательным
    # ставим ОГРОМНЫЙ штраф (выбрасывать только если иначе никак); любой
    # выброшенный обязательный всё равно покрыт одиночками/CW в общем пуле.
    mand_pen = max(opt_pen, int(round(w.vehicle_salary * COST_SCALE))) * 10000
    for node in range(1, n + 1):
        pen = opt_pen if orders[node - 1].optional else mand_pen
        routing.AddDisjunction([manager.NodeToIndex(node)], pen)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = getattr(
        routing_enums_pb2.FirstSolutionStrategy, first_solution
    )
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    params.time_limit.FromSeconds(int(time_budget))

    sol = routing.SolveWithParameters(params)
    if sol is None:
        print(f"[ortools] решение не найдено (status={routing.status()})")
        return []
    dropped = sum(
        1 for node in range(1, n + 1)
        if sol.Value(routing.NextVar(manager.NodeToIndex(node))) == manager.NodeToIndex(node)
    )
    if dropped:
        print(f"[ortools] выброшено заказов (не размещены): {dropped}")

    routes = []
    for v in range(num_vehicles):
        idx = routing.Start(v)
        seq = []
        while not routing.IsEnd(idx):
            node = manager.IndexToNode(idx)
            if node != 0:
                seq.append(node_oid[node])
            idx = sol.Value(routing.NextVar(idx))
        if seq:
            routes.append(seq)
    return routes


def generate_pool(scenario, num_restarts=200, deadline=None,
                  use_ortools=False, ortools_budget=150, seed_routes=None):
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

    # Внешние seed-маршруты (например, одноразовый OR-Tools вызов из
    # solve_pipeline, переиспользуемый всеми multi-start циклами):
    # добавляются в пул как обычные кандидаты через add() - валидация
    # eval_route гарантирует корректность, CP-SAT сам решит, брать ли.
    if seed_routes:
        before_seed = len(pool)
        for r in seed_routes:
            add(list(r))
        print(
            f"[pool/vehicles] seed-маршруты: подано {len(seed_routes)}, "
            f"в пул добавлено {len(pool) - before_seed}"
        )

    # OR-Tools Routing как ГЕНЕРАТОР плотных маршрутов в пул (под флагом).
    # Работает только в режиме смены 'min_duration' - иначе его маршруты не
    # пройдут eval_route в add() и пул не пополнится. Каждый его маршрут -
    # обычный кандидат: CP-SAT сам решит, брать ли. Добавление в пул не может
    # ухудшить оптимум CP-SAT, только даёт недостающие плотные варианты.
    # ВНИМАНИЕ: при multi-start этот путь вызывается в КАЖДОМ цикле и
    # жжёт пул-бюджет повторно - предпочтительнее одноразовый вызов в
    # solve_pipeline с передачей результата через seed_routes.
    if use_ortools:
        t_or = time.time()
        before = len(pool)
        ort_budget = ortools_budget
        if deadline is not None:
            ort_budget = max(1, min(ortools_budget, deadline - time.time() - 5))
        try:
            ort_routes = ortools_generate_routes(
                scenario, time_budget=ort_budget, deadline=deadline, by_id=by_id
            )
            for r in ort_routes:
                add(r)
            print(
                f"[pool/vehicles] OR-Tools: выдал {len(ort_routes)} маршрутов, "
                f"в пул добавлено {len(pool) - before} (прошли eval_route), "
                f"({time.time() - t_or:.1f}s)"
            )
        except Exception as e:  # noqa: BLE001
            print(f"[pool/vehicles] OR-Tools пропущен (ошибка: {e})")

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
                          reserve_after=0, pool_deadline=None,
                          use_ortools=False, ortools_budget=150, seed_routes=None):
    """pool_deadline - отдельный (обычно более узкий, чем общий deadline)
    дедлайн специально для generate_pool. Позволяет выделить пулу
    маршрутов свою долю общего бюджета времени, не давая ему съесть
    всё время, нужное CP-SAT/consolidate/грузчикам.

    use_ortools - добавить в пул плотные маршруты от OR-Tools Routing
    (требует режима смены 'min_duration', см. set_shift_mode)."""
    effective_pool_deadline = pool_deadline if pool_deadline is not None else deadline
    pool = generate_pool(scenario, num_restarts, deadline=effective_pool_deadline,
                         use_ortools=use_ortools, ortools_budget=ortools_budget,
                         seed_routes=seed_routes)
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