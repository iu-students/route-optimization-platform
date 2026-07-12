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
