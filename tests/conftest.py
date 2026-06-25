import pytest
from models import Scenario, Depot, Weights, Order


@pytest.fixture
def scenario():
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
