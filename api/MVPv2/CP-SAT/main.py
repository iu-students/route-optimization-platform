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
from vehicle_routes import find_vehicles_routes
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


def solve_with_feedback(scenario, v_restarts, l_restarts, on_stage=None):

    def stage(name):
        if on_stage:
            on_stage(name)

    stage("solving_vehicles")
    solution, missed_count = find_vehicles_routes(
        scenario, num_restarts=v_restarts, time_limit=240
    )
    solution["missed_optional_count"] = missed_count
    stage("solving_loaders")
    solution["loaders"] = find_loaders_routes(
        solution, scenario, num_restarts=l_restarts, time_limit=240
    )
    stats = calculate_statistics(solution, scenario)
    solution["statistics"] = stats
    print(f"[feedback] итерация 1: total_cost={stats['total_cost']:.2f}")
    bad_ids = find_bad_optional_orders(solution, scenario)
    if not bad_ids:
        print("[feedback] невыгодных optional-заказов нет, завершаем.")
        return solution
    print(f"[feedback] невыгодных optional-заказов: {len(bad_ids)} → {sorted(bad_ids)}")
    stage("feedback_iteration")
    reduced_scenario = build_reduced_scenario(scenario, bad_ids)
    v2 = max(1, v_restarts // 2)
    l2 = max(1, l_restarts // 2)
    solution2, missed_count2 = find_vehicles_routes(
        reduced_scenario, num_restarts=v2, time_limit=60
    )
    solution2["missed_optional_count"] = missed_count2 + len(bad_ids)
    solution2["loaders"] = find_loaders_routes(
        solution2, reduced_scenario, num_restarts=l2, time_limit=60
    )
    stats2 = calculate_statistics(solution2, scenario)
    solution2["statistics"] = stats2
    print(f"[feedback] итерация 2 (усечённая): total_cost={stats2['total_cost']:.2f}")
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


def solve_pipeline(input_path="data/input.json", output_path="data/output.json", on_stage=None):

    def stage(name):
        if on_stage:
            on_stage(name)

    t_start = time.time()
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
        f"[main] заказов={n} → vehicle_restarts={v_restarts}, loader_restarts={l_restarts}"
    )
    stage("solving")
    solution = solve_with_feedback(scenario, v_restarts, l_restarts, on_stage=on_stage)
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
    
    print(
        f"\n[ИТОГО] {time.time() - t_start:.1f}s, машин={len(solution['vehicles'])}, грузчиков={len(solution['loaders'])}"
    )
    return solution


if __name__ == "__main__":
    solve_pipeline(input_path="../../instances/i7.json", output_path="../../instances/output_i7.json")