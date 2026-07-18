# flake8: noqa: E501, E402, W291, W293, F541
import json
import time
import sys
import os

# Принудительная построчная буферизация вывода: при запуске с
# редиректом (docker logs, nohup, systemd/journald, pipe) Python
# буферизует stdout блоками по ~8KB, и прогресс-принты "копятся" молча,
# создавая впечатление, что решатель не работает. line_buffering
# заставляет каждый print уходить сразу (эквивалент запуска python -u).
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

_PARENT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
_SELF = os.path.dirname(os.path.abspath(__file__))
if _SELF not in sys.path:
    sys.path.insert(0, _SELF)

from Shared.models import Scenario, Depot, Weights, Order
from Web.validator import validate_input
from vehicle_routes import find_vehicles_routes, select_routes_from_pool, consolidate_routes, merge_multi_trip_routes, reduce_vehicles_by_merge, set_shift_mode, inter_route_local_search, eval_route, perturb_solution
from loader_routes import find_loaders_routes
from Shared.verifier import run_verification


def parse(path):
    with open(path) as f:
        raw = json.load(f)
    validate_input(raw)
    depot = Depot(**raw["depot"])
    weights = Weights(**raw["weights"])
    orders = [Order(**o) for o in raw["orders"]]
    print(
        f"[parse] {len(orders)} заказов, обяз={sum((1 for o in orders if not o.optional))}, опц={sum((1 for o in orders if o.optional))}"
    )
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


def evaluate_order_burden(solution, scenario, mode="conservative"):
    """Маргинальная выгода loader-стороны от удаления заказа.

    mode="conservative": полную стоимость цепочки засчитываем только если
    заказ - ЕДИНСТВЕННЫЙ в цепочке (цепочка исчезнет вместе с ним,
    экономия = loader_salary + work*lst). Если в цепочке есть другие
    заказы, удаление одного НЕ убирает зарплату грузчика - выгода ~0.
    НЕДООЦЕНИВАЕТ: не видит, что массовое удаление позволяет
    переупаковать цепочки и сократить их число.

    mode="aggressive": равномерное размазывание chain_cost/len(route) по
    заказам цепочки. ПЕРЕОЦЕНИВАЕТ: маргинальные экономии не аддитивны,
    зарплата цепочки не исчезает при удалении одного заказа.

    Истина между двумя оценками и зависит от инстанса, поэтому
    solve_with_feedback проверяет ОБА набора кандидатов фактическим
    перерешением и берёт лучший результат."""
    w = scenario.weights
    by_id = {o.id: o for o in scenario.orders}
    burden = {}
    for ld in solution["loaders"]:
        route = ld["route"]
        if not route:
            continue
        chain_cost = (
            w.loader_salary
            + w.loader_work * by_id[route[0]].loader_service_time
        )
        if mode == "aggressive":
            share = chain_cost / len(route)
            for oid in route:
                burden[oid] = burden.get(oid, 0.0) + share
        else:
            if len(route) == 1:
                oid = route[0]
                burden[oid] = burden.get(oid, 0.0) + chain_cost
    return burden


def evaluate_vehicle_marginal_savings(solution, scenario):
    """Точная маргинальная экономия vehicle-стороны от удаления каждого
    заказа из ТЕКУЩЕГО решения: насколько подешевеет маршрут (топливный
    крюк * fuel_cost), если этот заказ выкинуть из его последовательности,
    плюс полный vehicle_salary, если маршрут при этом опустеет.

    Зачем: до сих пор feedback умел отбрасывать невыгодные опциональные
    заказы только по стоимости ГРУЗЧИКОВ (evaluate_order_burden), а
    vehicle-сторону не видел вовсе. На инстансах с дешёвым штрафом
    (i1: optional_order_penalty=164 при fuel_cost=2) baseline выигрывает
    именно тем, что пропускает несколько дальних опциональных заказов,
    крюк до которых стоит дороже штрафа - мы же выполняли всё."""
    w = scenario.weights
    by_id = {o.id: o for o in scenario.orders}
    savings = {}
    for v in solution["vehicles"]:
        order_ids = [pid for pid in v["route"] if pid != 0]
        if not order_ids:
            continue
        base = eval_route(order_ids, scenario, by_id=by_id)
        if base is None:
            continue
        base_dist = base[2]
        for oid in order_ids:
            rest = [x for x in order_ids if x != oid]
            if not rest:
                # маршрут опустеет: экономим и топливо всего маршрута,
                # и зарплату машины целиком
                savings[oid] = base_dist * w.fuel_cost + w.vehicle_salary
                continue
            res = eval_route(rest, scenario, by_id=by_id)
            if res is None:
                # удаление сделало маршрут невалидным? (не должно, но
                # перестраховка) - экономию не засчитываем
                continue
            savings[oid] = (base_dist - res[2]) * w.fuel_cost
    return savings


def find_bad_optional_orders(solution, scenario, mode="conservative"):
    """Опциональный заказ помечается невыгодным, если суммарная
    маргинальная экономия от его удаления (точный топливный крюк по
    текущему маршруту + оценка loader-стороны в выбранном режиме)
    строго превышает optional_order_penalty."""
    burden = evaluate_order_burden(solution, scenario, mode=mode)
    veh_savings = evaluate_vehicle_marginal_savings(solution, scenario)
    by_id = {o.id: o for o in scenario.orders}
    penalty = scenario.weights.optional_order_penalty
    bad = set()
    for v in solution["vehicles"]:
        for oid in v["route"]:
            if oid == 0 or not by_id[oid].optional:
                continue
            total_gain = veh_savings.get(oid, 0.0) + burden.get(oid, 0.0)
            if total_gain > penalty:
                bad.add(oid)
    return bad


def build_reduced_scenario(scenario, exclude_ids):
    reduced_orders = [o for o in scenario.orders if o.id not in exclude_ids]
    return Scenario(
        depot=scenario.depot,
        weights=scenario.weights,
        orders=reduced_orders,
        vehicle_capacity=scenario.vehicle_capacity,
        vehicle_speed=scenario.vehicle_speed,
        loader_speed=scenario.loader_speed,
        vehicle_shift_size=scenario.vehicle_shift_size,
        loader_shift_size=scenario.loader_shift_size,
    )


def _remaining(deadline, reserve=0, floor=5):
    """Сколько секунд осталось до общего дедлайна, минус резерв на
    последующие этапы. Никогда не меньше floor."""
    if deadline is None:
        return None
    return max(floor, deadline - time.time() - reserve)


def solve_with_feedback(scenario, v_restarts, l_restarts, on_stage=None, run_feedback=True,
                         time_limit=240, deadline=None, use_ortools=False, ortools_budget=150,
                         pool_budget_vehicles=300, pool_budget_loaders=120,
                         seed_routes=None, stats_scenario=None):
    # stats_scenario - сценарий с РЕАЛЬНЫМИ весами для расчёта официальной
    # метрики и отбора лучшего варианта. Сам scenario может нести
    # искусственно завышенный optional_order_penalty (см.
    # optional_penalty_factor в solve_pipeline) - он влияет только на
    # внутреннюю оптимизацию (CP-SAT missed-штраф, пороги feedback),
    # но НЕ на сравнение результатов между собой.
    if stats_scenario is None:
        stats_scenario = scenario

    def stage(name):
        if on_stage:
            on_stage(name)

    # Резервы - грубая оценка, сколько времени нужно оставить на
    # последующие этапы ПОСЛЕ текущего CP-SAT вызова, чтобы не
    # выйти за общий дедлайн. CP-SAT time_limit при этом вычисляется
    # ВНУТРИ find_vehicles_routes/find_loaders_routes - уже ПОСЛЕ
    # построения пула, а не заранее (иначе время, потраченное на
    # пул, не будет учтено, и дедлайн можно превысить).
    RESERVE_AFTER_VEHICLE_CPSAT = 30   # consolidate + loaders + verification
    RESERVE_AFTER_LOADER_CPSAT = 5     # verification

    # Отдельный, более узкий тайм-бюджет специально на построение пула
    # маршрутов (не на весь этап целиком) - чтобы "больше маршрутов на
    # выбор" не съедало время, нужное CP-SAT/consolidate/грузчикам.
    # num_restarts при этом ставим заведомо большим - реальным
    # ограничителем становится именно этот тайм-бюджет, а не число
    # рестартов (см. deadline внутри generate_pool/generate_loader_pool).
    # Значения теперь ПАРАМЕТРЫ (масштабируются по размеру инстанса в
    # solve_pipeline): на малых инстансах пул за глаза наполняется за
    # десятки секунд, а сэкономленное время выгоднее пустить на
    # дополнительные multi-start попытки.
    POOL_TIME_BUDGET_VEHICLES = pool_budget_vehicles
    POOL_TIME_BUDGET_LOADERS = pool_budget_loaders
    UNBOUNDED_RESTARTS = 100000

    pool_deadline_vehicles = None
    pool_deadline_loaders = None
    if deadline is not None:
        pool_deadline_vehicles = min(
            deadline, time.time() + POOL_TIME_BUDGET_VEHICLES
        )
        pool_deadline_loaders = min(
            deadline, time.time() + POOL_TIME_BUDGET_LOADERS
        )

    stage("solving_vehicles")
    solution, missed_count, vehicle_pool = find_vehicles_routes(
        scenario, num_restarts=UNBOUNDED_RESTARTS, time_limit=time_limit,
        deadline=deadline, reserve_after=RESERVE_AFTER_VEHICLE_CPSAT,
        pool_deadline=pool_deadline_vehicles,
        use_ortools=use_ortools, ortools_budget=ortools_budget,
        seed_routes=seed_routes,
    )
    solution["missed_optional_count"] = missed_count
    stage("consolidating_vehicles")
    solution["vehicles"] = consolidate_routes(solution, scenario, deadline=deadline)["vehicles"]
    solution["vehicles"] = reduce_vehicles_by_merge(solution, scenario, deadline=deadline)["vehicles"]
    solution["vehicles"] = inter_route_local_search(solution, scenario, deadline=deadline)["vehicles"]
    solution["vehicles"] = merge_multi_trip_routes(solution, scenario, deadline=deadline)["vehicles"]
    stage("solving_loaders")
    if deadline is not None:
        pool_deadline_loaders = min(deadline, time.time() + POOL_TIME_BUDGET_LOADERS)
    solution["loaders"] = find_loaders_routes(
        solution, scenario, num_restarts=UNBOUNDED_RESTARTS, time_limit=time_limit,
        deadline=deadline, reserve_after=RESERVE_AFTER_LOADER_CPSAT,
        pool_deadline=pool_deadline_loaders,
    )
    stats = calculate_statistics(solution, stats_scenario)
    solution["statistics"] = stats
    print(f"[feedback] итерация 1: total_cost={stats['total_cost']:.2f}")

    if not run_feedback:
        print("[feedback] отключён (run_feedback=False), завершаем на итерации 1.")
        return solution

    # Если бюджета почти не осталось - не начинаем вторую итерацию вообще,
    # т.к. её тоже нужно уложить в общий дедлайн (пул-фильтр + CP-SAT +
    # consolidate + loaders).
    MIN_TIME_FOR_FEEDBACK = 20
    if deadline is not None and _remaining(deadline) <= MIN_TIME_FOR_FEEDBACK:
        print(
            f"[feedback] бюджета времени почти не осталось "
            f"(<{MIN_TIME_FOR_FEEDBACK}s), пропускаем итерацию 2."
        )
        return solution

    # Два кандидат-набора на исключение: консервативный (недооценивает
    # выгоду) и агрессивный (переоценивает). Какой лучше - зависит от
    # инстанса, поэтому проверяем ОБА фактическим перерешением (пул
    # фильтруется мгновенно, CP-SAT на урезанном пуле быстрый) и берём
    # лучший результат из трёх (итерация 1 / 2a / 2b).
    candidate_sets = []
    seen_sets = set()
    for mode in ("conservative", "aggressive"):
        ids = find_bad_optional_orders(solution, scenario, mode=mode)
        key = frozenset(ids)
        if ids and key not in seen_sets:
            seen_sets.add(key)
            candidate_sets.append((mode, ids))
    if not candidate_sets:
        print("[feedback] невыгодных optional-заказов нет, завершаем.")
        return solution
    stage("feedback_iteration")

    best = solution
    for mode, bad_ids in candidate_sets:
        if deadline is not None and _remaining(deadline) <= MIN_TIME_FOR_FEEDBACK:
            print("[feedback] времени на следующий кандидат-набор нет, стоп.")
            break
        print(
            f"[feedback/{mode}] невыгодных optional-заказов: {len(bad_ids)} → {sorted(bad_ids)}"
        )
        reduced_scenario = build_reduced_scenario(scenario, bad_ids)

        # Переиспользуем уже построенный пул маршрутов вместо генерации
        # нового - это самая дорогая часть. Обязательные заказы никогда
        # не попадают в bad_ids, поэтому фильтрация не ломает покрытие.
        t0 = time.time()
        filtered_pool = [
            r for r in vehicle_pool if not (set(r["order_ids"]) & bad_ids)
        ]
        print(
            f"[feedback/{mode}] пул отфильтрован: {len(vehicle_pool)} → {len(filtered_pool)} "
            f"маршрутов ({time.time() - t0:.2f}s, без перегенерации)"
        )

        solution2, missed_count2 = select_routes_from_pool(
            filtered_pool, reduced_scenario, time_limit=min(60, time_limit),
            deadline=deadline, reserve_after=RESERVE_AFTER_VEHICLE_CPSAT,
        )
        solution2["missed_optional_count"] = missed_count2 + len(bad_ids)
        solution2["vehicles"] = consolidate_routes(solution2, reduced_scenario, deadline=deadline)["vehicles"]
        solution2["vehicles"] = reduce_vehicles_by_merge(solution2, reduced_scenario, deadline=deadline)["vehicles"]
        solution2["vehicles"] = inter_route_local_search(solution2, reduced_scenario, deadline=deadline)["vehicles"]
        solution2["vehicles"] = merge_multi_trip_routes(solution2, reduced_scenario, deadline=deadline)["vehicles"]
        pool_deadline_loaders2 = None
        if deadline is not None:
            pool_deadline_loaders2 = min(deadline, time.time() + POOL_TIME_BUDGET_LOADERS // 2)
        solution2["loaders"] = find_loaders_routes(
            solution2, reduced_scenario, num_restarts=UNBOUNDED_RESTARTS, time_limit=min(60, time_limit),
            deadline=deadline, reserve_after=RESERVE_AFTER_LOADER_CPSAT,
            pool_deadline=pool_deadline_loaders2,
        )
        stats2 = calculate_statistics(solution2, stats_scenario)
        solution2["statistics"] = stats2
        print(f"[feedback/{mode}] total_cost={stats2['total_cost']:.2f}")
        if stats2["total_cost"] < best["statistics"]["total_cost"]:
            best = solution2

    print(
        f"[feedback] лучший вариант: total_cost={best['statistics']['total_cost']:.2f}"
    )
    return best


def calculate_statistics(solution, scenario):
    w = scenario.weights
    by_id = {o.id: o for o in scenario.orders}
    fuel_cost = sum((v["dist"] for v in solution["vehicles"])) * w.fuel_cost
    vehicle_salaries = len(solution["vehicles"]) * w.vehicle_salary
    loader_salaries = len(solution["loaders"]) * w.loader_salary
    # официальная метрика LoaderWorkTime (см. loader_routes.eval_chain):
    # loader_work * сумма loader_service_time ПЕРВОГО заказа каждого
    # грузчика - а не полная длительность смены. Считаем так же, чтобы
    # внутренние логи совпадали с официальным счётом валидатора.
    loader_work_cost = (
        sum(
            by_id[ld["route"][0]].loader_service_time
            for ld in solution["loaders"]
            if ld["route"]
        )
        * w.loader_work
    )
    penalties = solution.get("missed_optional_count", 0) * w.optional_order_penalty
    total_cost = (
        fuel_cost + vehicle_salaries + loader_salaries + loader_work_cost + penalties
    )
    return {
        "total_cost": total_cost,
        "fuel_cost": fuel_cost,
        "vehicle_salaries": vehicle_salaries,
        "loader_salaries": loader_salaries,
        "loader_work_cost": loader_work_cost,
        "penalties": penalties,
    }


def solve_pipeline(input_path="data/input.json", output_path="data/output.json", on_stage=None,
                    run_feedback=True, time_limit=240, max_total_time=840,
                    use_ortools=False, ortools_budget=10, shift_mode=None,
                    optional_penalty_factor=1.0):
    """max_total_time - общий бюджет времени в секундах на весь пайплайн
    (по умолчанию 840s = 14 минут, с запасом 60s от требования QR-004
    в 900s/15 минут - запас нужен на parsing/verification/запись файла,
    которые сами по себе не бюджетируются явным дедлайном).

    time_limit - потолок на один вызов CP-SAT (240s). Эмпирически на i4
    подъём до 510s не сдвинул objective (узкое место - не время решателя, а
    состав пула), поэтому держим 240s: это даёт CP-SAT достаточно и
    оставляет здоровый запас по общему дедлайну (итог ~540s из 840).

    shift_mode - явное управление режимом расчёта depart ('earliest' |
    'min_duration'), независимое от use_ortools. По умолчанию
    'min_duration': формула математически эквивалентна 'earliest', но
    минимизирует длительность смены вместо простого расчёта от окна
    первого заказа, за счёт чего плотные маршруты не бракуются ложно
    (см. merge_multi_trip_routes и _eval_route_mindur/_best_depart -
    обе функции теперь СОГласованно используют одну и ту же корректную
    формулу, включая защитный отступ от границы vehicle_shift_size).
    'earliest' оставлен только для отладки/сравнения."""

    effective_shift_mode = shift_mode
    if effective_shift_mode is None:
        effective_shift_mode = "min_duration"
    set_shift_mode(effective_shift_mode)
    print(f"[main] РЕЖИМ смены: {effective_shift_mode}"
          + (" + OR-Tools генератор" if use_ortools else ""))

    stage_times = []

    def stage(name):
        stage_times.append((name, time.time()))
        if on_stage:
            on_stage(name)

    t_start = time.time()
    deadline = t_start + max_total_time if max_total_time is not None else None

    stage("parsing")
    scenario = parse(input_path)
    n = len(scenario.orders)
    if n > 500:
        v_restarts, l_restarts = (50, 30)
    elif n > 200:
        v_restarts, l_restarts = (100, 60)
    else:
        v_restarts, l_restarts = (200, 100)
    # бюджеты пула масштабируем по размеру: на малых инстансах пул
    # наполняется за десятки секунд, а высвобожденное время выгоднее
    # пустить на multi-start (несколько независимых полных циклов с
    # выбором лучшего). Большие инстансы сохраняют прежние 300/120.
    if n <= 120:
        pool_bv, pool_bl = (60, 30)
        cycle_time_limit = min(time_limit, 60)
    elif n <= 250:
        pool_bv, pool_bl = (140, 60)
        cycle_time_limit = min(time_limit, 120)
    else:
        pool_bv, pool_bl = (300, 120)
        cycle_time_limit = time_limit
    print(
        f"[main] заказов={n} → vehicle_restarts={v_restarts}, loader_restarts={l_restarts}, "
        f"run_feedback={run_feedback}, time_limit={cycle_time_limit}, max_total_time={max_total_time}, "
        f"pool_budget=({pool_bv}, {pool_bl})"
    )

    # --- B: защита покрытия опциональных заказов (опциональная ручка) ---
    # optional_penalty_factor > 1 искусственно завышает штраф за пропуск
    # ТОЛЬКО для внутреннего оптимизатора (CP-SAT missed-штраф и пороги
    # feedback): решатель становится осторожнее с пропусками. Отбор
    # лучшего варианта (multi-start / feedback / polish) ВСЕГДА идёт по
    # реальной метрике (stats_scenario=scenario), так что фактор не может
    # незаметно ухудшить официальный total_cost - он лишь смещает, какие
    # кандидаты генерируются. Дефолт 1.0 = прежнее поведение.
    solve_scenario = scenario
    if optional_penalty_factor != 1.0:
        from dataclasses import replace as _dc_replace
        solve_scenario = _dc_replace(
            scenario,
            weights=_dc_replace(
                scenario.weights,
                optional_order_penalty=scenario.weights.optional_order_penalty
                * optional_penalty_factor,
            ),
        )
        print(f"[main] optional_penalty_factor={optional_penalty_factor} "
              f"(внутренний penalty={solve_scenario.weights.optional_order_penalty:.0f}, "
              f"метрика считается по реальному {scenario.weights.optional_order_penalty:.0f})")

    # --- A: одноразовый OR-Tools seed вместо перегенерации в каждом цикле ---
    # Раньше use_ortools=True вызывал OR-Tools генератор ВНУТРИ generate_pool,
    # т.е. в КАЖДОМ multi-start цикле заново (до ortools_budget секунд каждый
    # раз - чистая потеря пул-бюджета на повторную работу). Теперь генератор
    # вызывается ОДИН раз здесь, а его маршруты передаются во все циклы как
    # seed_routes (добавление в пул почти бесплатно).
    ortools_seed = None
    if use_ortools:
        try:
            from vehicle_routes import ortools_generate_routes
            t_or = time.time()
            ort_budget = ortools_budget
            if deadline is not None:
                ort_budget = max(1, min(ortools_budget, deadline - time.time() - 30))
            ortools_seed = ortools_generate_routes(
                solve_scenario, time_budget=ort_budget, deadline=deadline,
            )
            print(f"[main] OR-Tools seed: {len(ortools_seed)} маршрутов за "
                  f"{time.time() - t_or:.1f}s (одноразово, переиспользуется всеми циклами)")
        except Exception as e:  # noqa: BLE001
            print(f"[main] OR-Tools seed пропущен (ошибка: {e})")
            ortools_seed = None

    stage("solving")
    # --- MULTI-START -------------------------------------------------------
    # На малых инстансах (десятки-сотни заказов) один полный цикл решения
    # (пул до плато + CP-SAT + пост-обработка + грузчики) занимает лишь
    # малую часть бюджета времени, а результат от прогона к прогону гуляет
    # из-за стохастики эвристик (jitter в рестартах): на i1 baseline стоит
    # всего ~12k, так что +-1 машина/грузчик = +-3-6% total_cost - отсюда
    # "иногда лучше, иногда хуже baseline". Лекарство: пока остаётся время,
    # гоняем НЕЗАВИСИМЫЕ полные циклы (каждый с новым случайным пулом) и
    # берём лучший по официальной метрике. Дисперсия минимума из K попыток
    # существенно ниже дисперсии одной попытки. На больших инстансах первый
    # цикл съедает почти весь бюджет - multi-start автоматически
    # вырождается в текущее поведение (1 цикл), ничего не ломая.
    MULTISTART_OVERHEAD = 1.15  # запас на разброс длительности цикла
    MULTISTART_RESERVE = 20     # секунды на verification/запись файла
    best_solution = None
    best_cost = float("inf")
    attempt = 0
    pool_bv_cur, pool_bl_cur, tl_cur = pool_bv, pool_bl, cycle_time_limit
    while True:
        attempt += 1
        t_cycle = time.time()
        try:
            candidate = solve_with_feedback(
                solve_scenario, v_restarts, l_restarts, on_stage=stage,
                run_feedback=run_feedback, time_limit=tl_cur, deadline=deadline,
                use_ortools=False, ortools_budget=ortools_budget,
                pool_budget_vehicles=pool_bv_cur, pool_budget_loaders=pool_bl_cur,
                seed_routes=ortools_seed, stats_scenario=scenario,
            )
            cost = candidate["statistics"]["total_cost"]
        except Exception as e:  # noqa: BLE001
            # усечённая попытка на бедном пуле может не покрыть слоты
            # грузчиков (RuntimeError из loader CP-SAT) - попытка просто
            # отбрасывается, лучшие решения предыдущих попыток целы
            print(f"[multi-start] попытка {attempt} упала и отброшена: {e}")
            candidate = None
            cost = float("inf")
        cycle_dur = time.time() - t_cycle
        if cost < best_cost:
            best_cost = cost
            best_solution = candidate
            marker = "ЛУЧШЕЕ"
        else:
            marker = "хуже лучшего, отброшено"
        print(
            f"[multi-start] попытка {attempt}: total_cost={cost:.2f} "
            f"({cycle_dur:.1f}s) - {marker}"
        )
        if deadline is None:
            break
        remaining = deadline - time.time()
        # Раньше здесь был консервативный стоп: "остаток < полный цикл ×
        # 1.15 + резерв → выходим", из-за чего на малых/средних инстансах
        # 1-4 минуты бюджета простаивали. Теперь, пока остатка хватает хотя
        # бы на УСЕЧЁННУЮ попытку (MIN_ATTEMPT_TIME), запускаем ещё один
        # цикл с пул-бюджетами, смасштабированными под остаток. Усечённая
        # попытка с меньшим пулом может оказаться хуже - не страшно, её
        # отбросит выбор лучшего; может и выиграть за счёт другого
        # случайного пула. Остаток меньше MIN_ATTEMPT_TIME уходит в
        # LNS-полировку ниже.
        MIN_ATTEMPT_TIME = 90
        if remaining < cycle_dur * MULTISTART_OVERHEAD + MULTISTART_RESERVE:
            if remaining >= MIN_ATTEMPT_TIME:
                budget_for_attempt = remaining - MULTISTART_RESERVE
                att_bv = min(pool_bv, max(20, int(budget_for_attempt * 0.40)))
                att_bl = min(pool_bl, max(8, att_bv // 3))
                att_tl = min(cycle_time_limit, max(10, int(budget_for_attempt * 0.25)))
                if (pool_bv, pool_bl, cycle_time_limit) != (att_bv, att_bl, att_tl):
                    print(
                        f"[multi-start] остаток {remaining:.0f}s: усечённая попытка "
                        f"(pool=({att_bv}, {att_bl}), time_limit={att_tl})"
                    )
                pool_bv_cur, pool_bl_cur, tl_cur = att_bv, att_bl, att_tl
            else:
                print(
                    f"[multi-start] остаток {remaining:.0f}s < {MIN_ATTEMPT_TIME}s, "
                    f"переходим к LNS-полировке (всего попыток: {attempt}, "
                    f"лучший: {best_cost:.2f})"
                )
                break
        else:
            pool_bv_cur, pool_bl_cur, tl_cur = pool_bv, pool_bl, cycle_time_limit
    if best_solution is None:
        raise RuntimeError(
            "все multi-start попытки завершились ошибкой - решение не получено"
        )
    solution = best_solution

    # --- финальная полировка остатком времени -------------------------
    # multi-start выше выработал бюджет до последней усечённой попытки;
    # весь оставшийся хвост занимает LNS-петля (Large Neighborhood
    # Search): локальный поиск над лучшим решением → пересчёт грузчиков →
    # принять при строгом улучшении официальной метрики; если улучшения
    # нет - возмутить ЛУЧШЕЕ решение случайными допустимыми relocate-
    # ходами (perturb_solution) и искать снова. Петля крутится до самого
    # дедлайна, best монотонно не ухудшается.
    if deadline is not None and best_solution is not None:
        LNS_RESERVE = 15  # на verification + запись файла
        lns_rounds = 0
        lns_accepted = 0
        stagnant = 0
        current_vehicles = solution["vehicles"]
        while True:
            left = deadline - time.time() - LNS_RESERVE
            if left <= 25:
                break
            lns_rounds += 1
            try:
                cand = {
                    "vehicles": current_vehicles,
                    "missed_optional_count": solution.get("missed_optional_count", 0),
                }
                # полный scenario безопасен: локальный поиск не ДОБАВЛЯЕТ
                # заказов, только перемещает уже выбранные, так что
                # исключённые feedback'ом опциональные заказы не вернутся
                cand["vehicles"] = inter_route_local_search(
                    cand, scenario,
                    deadline=time.time() + min(left * 0.5, 60), max_passes=30,
                )["vehicles"]
                cand["vehicles"] = merge_multi_trip_routes(
                    cand, scenario, deadline=deadline - LNS_RESERVE
                )["vehicles"]
                cand["loaders"] = find_loaders_routes(
                    cand, scenario, num_restarts=100000,
                    time_limit=max(5, int(min(left * 0.3, 45))),
                    deadline=deadline - LNS_RESERVE // 2,
                    reserve_after=5,
                    pool_deadline=time.time() + min(left * 0.25, 25),
                )
                pstats = calculate_statistics(cand, scenario)
                cand["statistics"] = pstats
                if pstats["total_cost"] < best_cost - 1e-6:
                    print(
                        f"[lns] раунд {lns_rounds}: улучшение "
                        f"{best_cost:.2f} → {pstats['total_cost']:.2f}, принято"
                    )
                    solution = cand
                    best_cost = pstats["total_cost"]
                    current_vehicles = cand["vehicles"]
                    lns_accepted += 1
                    stagnant = 0
                    continue
                stagnant += 1
            except Exception as e:  # noqa: BLE001
                print(f"[lns] раунд {lns_rounds} пропущен ({e})")
                stagnant += 1
            # улучшения нет - возмущаем ЛУЧШЕЕ решение; сила возмущения
            # растёт с числом безуспешных раундов, чтобы выбираться из
            # более глубоких локальных оптимумов
            k = min(3 + stagnant // 2, 8)
            current_vehicles = perturb_solution(
                {"vehicles": solution["vehicles"]}, scenario, k=k
            )["vehicles"]
        if lns_rounds:
            print(
                f"[lns] раундов: {lns_rounds}, принято улучшений: {lns_accepted}, "
                f"финальный total_cost: {best_cost:.2f}"
            )
    stats = solution["statistics"]
    print(f"\n[статистика]")
    print(f"  fuel_cost:        {stats['fuel_cost']:.2f}")
    print(f"  vehicle_salaries: {stats['vehicle_salaries']:.2f}")
    print(f"  loader_salaries:  {stats['loader_salaries']:.2f}")
    print(f"  loader_work_cost: {stats['loader_work_cost']:.2f}")
    print(f"  penalties:        {stats['penalties']:.2f}")
    print(f"  total_cost:       {stats['total_cost']:.2f}")
    
    with open(output_path, "w") as f:
        json.dump(solution, f, indent=4)

    verification = run_verification(input_path=input_path, output_path=output_path)
    solution["verification"] = verification

    with open(output_path, "w") as f:
        json.dump(solution, f, indent=4)

    stage("done")

    total_elapsed = time.time() - t_start
    print(f"\n[тайминг по этапам]")
    prev_name, prev_time = "start", t_start
    for name, ts in stage_times:
        print(f"  {prev_name + ' → ' + name:40s} {ts - prev_time:8.2f}s")
        prev_name, prev_time = name, ts
    print(f"  {'итого':40s} {total_elapsed:8.2f}s")

    print(
        f"\n[ИТОГО] {total_elapsed:.1f}s, машин={len(solution['vehicles'])}, грузчиков={len(solution['loaders'])}"
    )
    return solution


if __name__ == "__main__":
    import sys as _sys
    no_feedback = "--no-feedback" in _sys.argv
    use_ortools = "--ortools" in _sys.argv
    solve_pipeline(
        input_path="instances/i1.json",
        output_path="instances/output_i1.json",
        run_feedback=not no_feedback,
        use_ortools=True,
    ) 