# flake8: noqa: E501, E402, W291, W293, F541
import json
import time
import sys
import os

_PARENT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
_SELF = os.path.dirname(os.path.abspath(__file__))
if _SELF not in sys.path:
    sys.path.insert(0, _SELF)

from Shared.models import Scenario, Depot, Weights, Order
from Web.validator import validate_input
from vehicle_routes import find_vehicles_routes, select_routes_from_pool, consolidate_routes, merge_multi_trip_routes
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


def evaluate_order_burden(solution, scenario):
    w = scenario.weights
    burden = {}
    for ld in solution["loaders"]:
        route = ld["route"]
        if not route:
            continue
        chain_cost = w.loader_salary + w.loader_work * ld["shift"]
        share = chain_cost / len(route)
        for oid in route:
            burden[oid] = burden.get(oid, 0.0) + share
    return burden


def find_bad_optional_orders(solution, scenario):
    burden = evaluate_order_burden(solution, scenario)
    by_id = {o.id: o for o in scenario.orders}
    bad = {
        oid
        for oid, b in burden.items()
        if by_id[oid].optional and b > scenario.weights.optional_order_penalty
    }
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
                         time_limit=240, deadline=None):

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
    POOL_TIME_BUDGET_VEHICLES = 300
    POOL_TIME_BUDGET_LOADERS = 120
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
    )
    solution["missed_optional_count"] = missed_count
    stage("consolidating_vehicles")
    solution["vehicles"] = consolidate_routes(solution, scenario, deadline=deadline)["vehicles"]
    solution["vehicles"] = merge_multi_trip_routes(solution, scenario, deadline=deadline)["vehicles"]
    stage("solving_loaders")
    if deadline is not None:
        pool_deadline_loaders = min(deadline, time.time() + POOL_TIME_BUDGET_LOADERS)
    solution["loaders"] = find_loaders_routes(
        solution, scenario, num_restarts=UNBOUNDED_RESTARTS, time_limit=time_limit,
        deadline=deadline, reserve_after=RESERVE_AFTER_LOADER_CPSAT,
        pool_deadline=pool_deadline_loaders,
    )
    stats = calculate_statistics(solution, scenario)
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

    bad_ids = find_bad_optional_orders(solution, scenario)
    if not bad_ids:
        print("[feedback] невыгодных optional-заказов нет, завершаем.")
        return solution
    print(f"[feedback] невыгодных optional-заказов: {len(bad_ids)} → {sorted(bad_ids)}")
    stage("feedback_iteration")

    reduced_scenario = build_reduced_scenario(scenario, bad_ids)

    # Переиспользуем уже построенный пул маршрутов вместо генерации нового -
    # это самая дорогая часть (insertion_construct/clarke_wright с num_restarts).
    # Обязательные заказы никогда не попадают в bad_ids (see find_bad_optional_orders),
    # поэтому фильтрация не ломает покрытие обязательных заказов.
    t0 = time.time()
    filtered_pool = [
        r for r in vehicle_pool if not (set(r["order_ids"]) & bad_ids)
    ]
    print(
        f"[feedback] пул отфильтрован: {len(vehicle_pool)} → {len(filtered_pool)} "
        f"маршрутов ({time.time() - t0:.2f}s, без перегенерации)"
    )

    solution2, missed_count2 = select_routes_from_pool(
        filtered_pool, reduced_scenario, time_limit=min(60, time_limit),
        deadline=deadline, reserve_after=RESERVE_AFTER_VEHICLE_CPSAT,
    )
    solution2["missed_optional_count"] = missed_count2 + len(bad_ids)
    solution2["vehicles"] = consolidate_routes(solution2, reduced_scenario, deadline=deadline)["vehicles"]
    solution2["vehicles"] = merge_multi_trip_routes(solution2, reduced_scenario, deadline=deadline)["vehicles"]
    pool_deadline_loaders2 = None
    if deadline is not None:
        pool_deadline_loaders2 = min(deadline, time.time() + POOL_TIME_BUDGET_LOADERS // 2)
    solution2["loaders"] = find_loaders_routes(
        solution2, reduced_scenario, num_restarts=UNBOUNDED_RESTARTS, time_limit=min(60, time_limit),
        deadline=deadline, reserve_after=RESERVE_AFTER_LOADER_CPSAT,
        pool_deadline=pool_deadline_loaders2,
    )
    stats2 = calculate_statistics(solution2, scenario)
    solution2["statistics"] = stats2
    print(f"[feedback] итерация 2 (усечённая, пул переиспользован): total_cost={stats2['total_cost']:.2f}")
    if stats2["total_cost"] < stats["total_cost"]:
        print("[feedback] итерация 2 лучше, используем её.")
        return solution2
    print("[feedback] итерация 1 лучше, оставляем её.")
    return solution


def calculate_statistics(solution, scenario):
    w = scenario.weights
    fuel_cost = sum((v["dist"] for v in solution["vehicles"])) * w.fuel_cost
    vehicle_salaries = len(solution["vehicles"]) * w.vehicle_salary
    loader_salaries = len(solution["loaders"]) * w.loader_salary
    loader_work_cost = sum((ld["shift"] for ld in solution["loaders"])) * w.loader_work
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
                    run_feedback=True, time_limit=240, max_total_time=840):
    """max_total_time - общий бюджет времени в секундах на весь пайплайн
    (по умолчанию 840s = 14 минут, с запасом 60s от требования QR-004
    в 900s/15 минут - запас нужен на parsing/verification/запись файла,
    которые сами по себе не бюджетируются явным дедлайном)."""

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
    print(
        f"[main] заказов={n} → vehicle_restarts={v_restarts}, loader_restarts={l_restarts}, "
        f"run_feedback={run_feedback}, time_limit={time_limit}, max_total_time={max_total_time}"
    )
    stage("solving")
    solution = solve_with_feedback(
        scenario, v_restarts, l_restarts, on_stage=stage,
        run_feedback=run_feedback, time_limit=time_limit, deadline=deadline,
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
    solve_pipeline(
        input_path="instances/i10.json",
        output_path="instances/output_i10.json",
        run_feedback=not no_feedback,
    )