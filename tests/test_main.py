import pytest
from vehicle_routes import find_distance, eval_route, best_insertion_pos, insertion_construct, clarke_wright
from loader_routes import build_slots, eval_chain, chains_insertion_construct
from models import Scenario, Depot, Weights, Order


def small_scenario():
    depot = Depot(x=0, y=0, load_time=0)
    weights = Weights(
        optional_order_penalty=1000,
        vehicle_salary=100,
        loader_salary=50,
        fuel_cost=2,
        loader_work=1,
    )
    orders = [
        Order(id=1, x=3, y=4, volume=5, time_window=(0, 50),
              vehicle_service_time=2, loader_cnt=1, loader_service_time=10, optional=0),
        Order(id=2, x=6, y=8, volume=4, time_window=(0, 80),
              vehicle_service_time=3, loader_cnt=0, loader_service_time=5, optional=0),
    ]
    return Scenario(
        vehicle_capacity=10, vehicle_speed=1, loader_speed=1,
        vehicle_shift_size=100, loader_shift_size=100,
        depot=depot, weights=weights, orders=orders,
    )


# find_distance

def test_find_distance():
    assert find_distance(0, 0, 3, 4) == 5.0


def test_find_distance_same_point():
    assert find_distance(2, 2, 2, 2) == 0.0


# eval_route

def test_eval_route_valid(scenario):
    result = eval_route([1], scenario)
    assert result is not None
    arrival_times, dist, return_time = result
    assert arrival_times == [5.0]


def test_eval_route_two_orders(scenario):
    result = eval_route([1, 2], scenario)
    assert result is not None
    arrival_times, dist, return_time = result
    assert arrival_times == [5.0, 12.0]


def test_eval_route_capacity_violation():
    sc = small_scenario()
    sc.vehicle_capacity = 5  # orders 1 and 2 together have volume 9
    assert eval_route([1, 2], sc) is None


def test_eval_route_time_window_violation():
    depot = Depot(x=0, y=0, load_time=0)
    weights = Weights(1000, 100, 50, 2, 1)
    orders = [Order(id=1, x=100, y=0, volume=1, time_window=(0, 5),
                    vehicle_service_time=0, loader_cnt=0,
                    loader_service_time=0, optional=0)]
    sc = Scenario(10, 1, 1, 1000, 1000, depot, weights, orders)
    assert eval_route([1], sc) is None


def test_eval_route_shift_violation():
    depot = Depot(x=0, y=0, load_time=0)
    weights = Weights(1000, 100, 50, 2, 1)
    orders = [Order(id=1, x=100, y=0, volume=1, time_window=(0, 1000),
                    vehicle_service_time=0, loader_cnt=0,
                    loader_service_time=0, optional=0)]
    sc = Scenario(10, 1, 1, 50, 1000, depot, weights, orders)
    assert eval_route([1], sc) is None


# best_insertion_pos

def test_best_insertion_pos_finds_position(scenario):
    result = best_insertion_pos([1], 2, scenario)
    assert result is not None
    pos, res = result
    assert pos in (0, 1)
    assert res is not None


def test_best_insertion_pos_no_feasible_insertion():
    depot = Depot(x=0, y=0, load_time=0)
    weights = Weights(1000, 100, 50, 2, 1)
    orders = [
        Order(id=1, x=1, y=0, volume=5, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0,
              loader_service_time=0, optional=0),
        Order(id=2, x=2, y=0, volume=10, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0,
              loader_service_time=0, optional=0),
    ]
    sc = Scenario(10, 1, 1, 1000, 1000, depot, weights, orders)
    assert best_insertion_pos([1], 2, sc) is None


# insertion_construct

def test_insertion_construct_covers_all_orders(scenario):
    routes = insertion_construct(scenario)
    served = set()
    for r in routes:
        served.update(r)
    assert served == {1, 2}


def test_insertion_construct_routes_are_feasible(scenario):
    routes = insertion_construct(scenario)
    for r in routes:
        assert eval_route(r, scenario) is not None


# clarke_wright

def test_clarke_wright_covers_all_orders(scenario):
    routes = clarke_wright(scenario)
    served = set()
    for r in routes:
        served.update(r)
    assert served == {1, 2}


def test_clarke_wright_routes_are_feasible(scenario):
    routes = clarke_wright(scenario)
    for r in routes:
        assert eval_route(r, scenario) is not None


# build_slots

def test_build_slots(scenario):
    solution = {
        "vehicles": [
            {"id": 1, "route": [0, 1, 2, 0], "time": [5.0, 12.0]}
        ]
    }
    slots = build_slots(solution, scenario)
    assert len(slots) == 1
    assert slots[0]["order_id"] == 1
    assert slots[0]["start"] == 5.0
    assert slots[0]["service"] == 10


def test_build_slots_no_loaders_needed():
    depot = Depot(x=0, y=0, load_time=0)
    weights = Weights(1000, 100, 50, 2, 1)
    orders = [Order(id=1, x=1, y=0, volume=1, time_window=(0, 100),
                    vehicle_service_time=1, loader_cnt=0,
                    loader_service_time=0, optional=0)]
    sc = Scenario(10, 1, 1, 100, 100, depot, weights, orders)
    solution = {"vehicles": [{"id": 1, "route": [0, 1, 0], "time": [1.0]}]}
    assert build_slots(solution, sc) == []


# eval_chain

def test_eval_chain_single_slot(scenario):
    slots = [
        {"slot_id": 0, "order_id": 1, "x": 3, "y": 4, "start": 5.0, "service": 10},
    ]
    result = eval_chain([0], slots, scenario)
    assert result is not None
    cost, shift = result
    assert cost == 60.0  # 50 (loader_salary) + 1 * 10 = 60


def test_eval_chain_two_slots_feasible(scenario):
    slots = [
        {"slot_id": 0, "order_id": 1, "x": 0, "y": 0, "start": 0.0, "service": 5},
        {"slot_id": 1, "order_id": 2, "x": 3, "y": 4, "start": 20.0, "service": 5},
    ]
    result = eval_chain([0, 1], slots, scenario)
    assert result is not None
    cost, shift = result
    assert cost > 0


def test_eval_chain_arrival_too_late(scenario):
    slots = [
        {"slot_id": 0, "order_id": 1, "x": 0, "y": 0, "start": 0.0, "service": 5},
        {"slot_id": 1, "order_id": 2, "x": 100, "y": 0, "start": 10.0, "service": 5},
    ]
    assert eval_chain([0, 1], slots, scenario) is None


def test_eval_chain_shift_violation():
    depot = Depot(x=0, y=0, load_time=0)
    weights = Weights(1000, 100, 50, 2, 1)
    orders = [Order(id=1, x=0, y=0, volume=1, time_window=(0, 1000),
                    vehicle_service_time=0, loader_cnt=1,
                    loader_service_time=0, optional=0)]
    sc = Scenario(10, 1, 1, 1000, 50, depot, weights, orders)
    slots = [
        {"slot_id": 0, "order_id": 1, "x": 0, "y": 0, "start": 0.0, "service": 100},
    ]
    assert eval_chain([0], slots, sc) is None


def test_eval_chain_empty():
    sc = small_scenario()
    assert eval_chain([], [], sc) is None


# chains_insertion_construct

def test_chains_insertion_construct_covers_all_slots(scenario):
    slots = [
        {"slot_id": 0, "order_id": 1, "x": 0, "y": 0, "start": 0.0, "service": 5},
        {"slot_id": 1, "order_id": 2, "x": 1, "y": 1, "start": 10.0, "service": 5},
    ]
    chains = chains_insertion_construct(slots, scenario)
    covered = set()
    for chain, result in chains:
        for sid in chain:
            covered.add(sid)
    assert covered == {0, 1}


def test_chains_insertion_construct_no_duplicate_orders(scenario):
    slots = [
        {"slot_id": 0, "order_id": 1, "x": 0, "y": 0, "start": 0.0, "service": 5},
        {"slot_id": 1, "order_id": 1, "x": 0, "y": 0, "start": 0.0, "service": 5},
    ]
    chains = chains_insertion_construct(slots, scenario)
    for chain, result in chains:
        order_ids = [slots[s]["order_id"] for s in chain]
        assert len(order_ids) == len(set(order_ids))


# ---------------------------------------------------------------------------
# main.py — вспомогательные функции (чистая логика, без CP-SAT)
# ---------------------------------------------------------------------------
import json
import tempfile
import os
import time
from main import (
    _remaining,
    build_reduced_scenario,
    calculate_statistics,
    evaluate_order_burden,
    evaluate_vehicle_marginal_savings,
    find_bad_optional_orders,
    solve_with_feedback,
    parse,
)
from vehicle_routes import set_shift_mode
set_shift_mode("earliest")


def _make_scenario(orders=None, weights=None):
    depot = Depot(x=0, y=0, load_time=0)
    if weights is None:
        weights = Weights(optional_order_penalty=1000, vehicle_salary=100,
                          loader_salary=50, fuel_cost=2, loader_work=1)
    if orders is None:
        orders = [
            Order(id=1, x=3, y=4, volume=5, time_window=(0, 50),
                  vehicle_service_time=2, loader_cnt=1, loader_service_time=10, optional=False),
        ]
    return Scenario(vehicle_capacity=10, vehicle_speed=1, loader_speed=1,
                    vehicle_shift_size=100, loader_shift_size=100,
                    depot=depot, weights=weights, orders=orders)


# _remaining

def test_remaining_no_deadline():
    assert _remaining(None) is None


def test_remaining_floor():
    assert _remaining(time.time() - 100) == 5


def test_remaining_with_reserve():
    deadline = time.time() + 50
    rem = _remaining(deadline, reserve=10)
    assert 35 <= rem <= 45


# build_reduced_scenario

def test_build_reduced_scenario_excludes_ids():
    orders = [
        Order(id=1, x=0, y=0, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0, loader_service_time=0, optional=False),
        Order(id=2, x=1, y=1, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0, loader_service_time=0, optional=False),
        Order(id=3, x=2, y=2, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0, loader_service_time=0, optional=False),
    ]
    sc = _make_scenario(orders=orders)
    reduced = build_reduced_scenario(sc, {2})
    ids = [o.id for o in reduced.orders]
    assert ids == [1, 3]


def test_build_reduced_scenario_preserves_other_fields():
    orders = [
        Order(id=1, x=0, y=0, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0, loader_service_time=0, optional=False),
        Order(id=2, x=1, y=1, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0, loader_service_time=0, optional=False),
    ]
    sc = _make_scenario(orders=orders)
    reduced = build_reduced_scenario(sc, {2})
    assert reduced.vehicle_capacity == sc.vehicle_capacity
    assert reduced.vehicle_speed == sc.vehicle_speed
    assert reduced.depot == sc.depot
    assert reduced.weights == sc.weights


# calculate_statistics

def test_calculate_statistics_basic():
    w = Weights(optional_order_penalty=1000, vehicle_salary=100,
                loader_salary=50, fuel_cost=2, loader_work=1)
    depot = Depot(x=0, y=0, load_time=0)
    orders = [
        Order(id=1, x=0, y=0, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=1, loader_service_time=10, optional=False),
    ]
    sc = Scenario(vehicle_capacity=10, vehicle_speed=1, loader_speed=1,
                  vehicle_shift_size=100, loader_shift_size=100,
                  depot=depot, weights=w, orders=orders)
    solution = {
        "vehicles": [{"route": [0, 1, 0], "dist": 5.0}],
        "loaders": [{"route": [1]}],
        "missed_optional_count": 0,
    }
    stats = calculate_statistics(solution, sc)
    assert stats["fuel_cost"] == 10.0       # 5 * 2
    assert stats["vehicle_salaries"] == 100
    assert stats["loader_salaries"] == 50
    assert stats["loader_work_cost"] == 10  # 1 * 10
    assert stats["penalties"] == 0
    assert stats["total_cost"] == 170.0


def test_calculate_statistics_with_penalty():
    w = Weights(optional_order_penalty=500, vehicle_salary=100,
                loader_salary=50, fuel_cost=2, loader_work=1)
    depot = Depot(x=0, y=0, load_time=0)
    orders = [
        Order(id=1, x=0, y=0, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0, loader_service_time=0, optional=False),
    ]
    sc = Scenario(vehicle_capacity=10, vehicle_speed=1, loader_speed=1,
                  vehicle_shift_size=100, loader_shift_size=100,
                  depot=depot, weights=w, orders=orders)
    solution = {
        "vehicles": [{"route": [0, 1, 0], "dist": 0.0}],
        "loaders": [],
        "missed_optional_count": 2,
    }
    stats = calculate_statistics(solution, sc)
    assert stats["penalties"] == 1000
    assert stats["total_cost"] == 100 + 0 + 0 + 0 + 1000


def test_calculate_statistics_empty_loader_route():
    w = Weights(optional_order_penalty=1000, vehicle_salary=100,
                loader_salary=50, fuel_cost=2, loader_work=1)
    depot = Depot(x=0, y=0, load_time=0)
    orders = [
        Order(id=1, x=0, y=0, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=1, loader_service_time=10, optional=False),
    ]
    sc = Scenario(vehicle_capacity=10, vehicle_speed=1, loader_speed=1,
                  vehicle_shift_size=100, loader_shift_size=100,
                  depot=depot, weights=w, orders=orders)
    solution = {
        "vehicles": [{"route": [0, 1, 0], "dist": 0.0}],
        "loaders": [{"route": []}],
        "missed_optional_count": 0,
    }
    stats = calculate_statistics(solution, sc)
    assert stats["loader_work_cost"] == 0
    assert stats["loader_salaries"] == 50


# evaluate_order_burden

def test_evaluate_order_burden_conservative_single():
    sc = _make_scenario()
    solution = {
        "loaders": [
            {"route": [1]},
        ],
    }
    burden = evaluate_order_burden(solution, sc, mode="conservative")
    assert burden == {1: 60.0}  # 50 (loader_salary) + 1 * 10


def test_evaluate_order_burden_conservative_multi():
    orders = [
        Order(id=1, x=0, y=0, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=1, loader_service_time=10, optional=False),
        Order(id=2, x=1, y=1, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=1, loader_service_time=5, optional=False),
    ]
    sc = _make_scenario(orders=orders)
    solution = {
        "loaders": [
            {"route": [1, 2]},
        ],
    }
    burden = evaluate_order_burden(solution, sc, mode="conservative")
    assert burden == {}  # chain length > 1, no savings in conservative mode


def test_evaluate_order_burden_aggressive():
    orders = [
        Order(id=1, x=0, y=0, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=1, loader_service_time=10, optional=False),
        Order(id=2, x=1, y=1, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=1, loader_service_time=5, optional=False),
    ]
    sc = _make_scenario(orders=orders)
    solution = {
        "loaders": [
            {"route": [1, 2]},
        ],
    }
    burden = evaluate_order_burden(solution, sc, mode="aggressive")
    # chain_cost = 50 + 1 * 10 = 60, share = 60 / 2 = 30 each
    assert burden == {1: 30.0, 2: 30.0}


def test_evaluate_order_burden_empty_route():
    sc = _make_scenario()
    solution = {
        "loaders": [
            {"route": []},
        ],
    }
    burden = evaluate_order_burden(solution, sc, mode="conservative")
    assert burden == {}


# evaluate_vehicle_marginal_savings

def test_evaluate_vehicle_marginal_savings_basic():
    depot = Depot(x=0, y=0, load_time=0)
    w = Weights(optional_order_penalty=1000, vehicle_salary=100,
                loader_salary=50, fuel_cost=2, loader_work=1)
    orders = [
        Order(id=1, x=0, y=0, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0, loader_service_time=0, optional=False),
        Order(id=2, x=3, y=4, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0, loader_service_time=0, optional=False),
    ]
    sc = Scenario(vehicle_capacity=10, vehicle_speed=1, loader_speed=1,
                  vehicle_shift_size=100, loader_shift_size=100,
                  depot=depot, weights=w, orders=orders)
    solution = {
        "vehicles": [
            {"route": [0, 1, 2, 0], "time": [0.0, 5.0, 10.0]},
        ],
    }
    savings = evaluate_vehicle_marginal_savings(solution, sc)
    # route [1,2] distance = 0 + 5 + 5 = 10
    # route [1] distance = 0 + 0 = 0
    # route [2] distance = 5 + 5 = 10
    # savings[1] = (10 - 10) * 2 = 0
    assert savings[1] == 0.0
    # savings[2] = (10 - 0) * 2 = 20
    assert savings[2] == 20.0


def test_evaluate_vehicle_marginal_savings_empty_route():
    sc = _make_scenario()
    solution = {
        "vehicles": [
            {"route": [0, 0], "time": [0.0]},
        ],
    }
    savings = evaluate_vehicle_marginal_savings(solution, sc)
    assert savings == {}


def test_evaluate_vehicle_marginal_savings_removing_empties_route():
    depot = Depot(x=0, y=0, load_time=0)
    w = Weights(optional_order_penalty=1000, vehicle_salary=100,
                loader_salary=50, fuel_cost=2, loader_work=1)
    orders = [
        Order(id=1, x=3, y=4, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0, loader_service_time=0, optional=False),
    ]
    sc = Scenario(vehicle_capacity=10, vehicle_speed=1, loader_speed=1,
                  vehicle_shift_size=1000, loader_shift_size=100,
                  depot=depot, weights=w, orders=orders)
    solution = {
        "vehicles": [
            {"route": [0, 1, 0], "time": [5.0]},
        ],
    }
    savings = evaluate_vehicle_marginal_savings(solution, sc)
    # Removing 1 empties the route → savings = dist * fuel + vehicle_salary
    # dist = 5 + 5 = 10, fuel=2, so 10*2 + 100 = 120
    assert savings[1] == 120.0


# find_bad_optional_orders

def test_find_bad_optional_orders_marks_expensive():
    depot = Depot(x=0, y=0, load_time=0)
    w = Weights(optional_order_penalty=50, vehicle_salary=100,
                loader_salary=50, fuel_cost=2, loader_work=1)
    orders = [
        Order(id=1, x=0, y=0, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=1, loader_service_time=10, optional=False),
        Order(id=2, x=100, y=0, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0, loader_service_time=0, optional=True),
    ]
    sc = Scenario(vehicle_capacity=10, vehicle_speed=1, loader_speed=1,
                  vehicle_shift_size=1000, loader_shift_size=100,
                  depot=depot, weights=w, orders=orders)
    solution = {
        "vehicles": [
            {"route": [0, 1, 2, 0], "time": [0.0, 100.0, 200.0]},
        ],
        "loaders": [
            {"route": [1]},
        ],
    }
    bad = find_bad_optional_orders(solution, sc, mode="conservative")
    # vehicle savings for removing 2: route [1,2] dist = 100+100+100 = 300,
    #     route [1] dist = 0 + 0 = 0, savings = 300*2 = 600
    # loader burden for 2: none (chain has one order = 1)
    # total gain = 600 > penalty(50) → marked bad
    assert 2 in bad


def test_find_bad_optional_orders_keeps_cheap():
    depot = Depot(x=0, y=0, load_time=0)
    w = Weights(optional_order_penalty=1000, vehicle_salary=100,
                loader_salary=50, fuel_cost=2, loader_work=1)
    orders = [
        Order(id=1, x=0, y=0, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=1, loader_service_time=10, optional=False),
        Order(id=2, x=0, y=0, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0, loader_service_time=0, optional=True),
    ]
    sc = Scenario(vehicle_capacity=10, vehicle_speed=1, loader_speed=1,
                  vehicle_shift_size=1000, loader_shift_size=100,
                  depot=depot, weights=w, orders=orders)
    solution = {
        "vehicles": [
            {"route": [0, 1, 2, 0], "time": [0.0, 0.0, 0.0]},
        ],
        "loaders": [
            {"route": [1]},
        ],
    }
    bad = find_bad_optional_orders(solution, sc, mode="conservative")
    # savings ≈ 0, penalty = 1000 → not bad
    assert 2 not in bad
    assert len(bad) == 0


# parse

def test_parse(tmpdir):
    input_data = {
        "depot": {"x": 0, "y": 0, "load_time": 0},
        "weights": {
            "optional_order_penalty": 1000,
            "vehicle_salary": 100,
            "loader_salary": 50,
            "fuel_cost": 2,
            "loader_work": 1,
        },
        "orders": [
            {
                "id": 1, "x": 3, "y": 4, "volume": 5,
                "time_window": [0, 50],
                "vehicle_service_time": 2, "loader_cnt": 1,
                "loader_service_time": 10, "optional": 0,
            },
        ],
        "vehicle_capacity": 10,
        "vehicle_speed": 1,
        "loader_speed": 1,
        "vehicle_shift_size": 100,
        "loader_shift_size": 100,
    }
    path = os.path.join(tmpdir, "input.json")
    with open(path, "w") as f:
        json.dump(input_data, f)
    scenario = parse(path)
    assert len(scenario.orders) == 1
    assert scenario.orders[0].x == 3


# solve_with_feedback — ранние выходы без вызова CP-SAT

def test_solve_with_feedback_no_feedback():
    sc = _make_scenario()
    # run_feedback=False → выход после первой итерации
    # time_limit=0 → solver не успевает, но мы проверяем только возврат
    sol = solve_with_feedback(sc, v_restarts=1, l_restarts=1,
                              run_feedback=False, time_limit=0)
    assert sol is not None
    assert "statistics" in sol


def test_solve_with_feedback_no_bad_orders():
    depot = Depot(x=0, y=0, load_time=0)
    w = Weights(optional_order_penalty=1000, vehicle_salary=100,
                loader_salary=50, fuel_cost=2, loader_work=1)
    orders = [
        Order(id=1, x=0, y=0, volume=1, time_window=(0, 100),
              vehicle_service_time=0, loader_cnt=0, loader_service_time=0, optional=False),
    ]
    sc = Scenario(vehicle_capacity=10, vehicle_speed=1, loader_speed=1,
                  vehicle_shift_size=100, loader_shift_size=100,
                  depot=depot, weights=w, orders=orders)
    sol = solve_with_feedback(sc, v_restarts=1, l_restarts=1,
                              run_feedback=True, time_limit=0,
                              pool_budget_vehicles=1, pool_budget_loaders=1)
    assert sol is not None
    assert "statistics" in sol
