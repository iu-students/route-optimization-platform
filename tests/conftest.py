import pytest
import os
import sys
import json
import tempfile

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

MVPv1_PATH = os.path.join(PROJECT_ROOT, "api", "MVPv1")
sys.path.insert(1, MVPv1_PATH)

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


@pytest.fixture
def app():
    TEST_API_KEY = "test-api-key-123"

    with tempfile.TemporaryDirectory() as tmpdir:
        import api.MVPv1.app as flask_app

        flask_app.API_KEY = TEST_API_KEY
        flask_app.DATA_DIR = tmpdir
        flask_app.INPUT_PATH = os.path.join(tmpdir, "input.json")
        flask_app.SOLUTION_PATH = os.path.join(tmpdir, "output.json")
        flask_app.solver_state = {"status": "idle"}

        def _mock_run_solve():
            with flask_app.solver_lock:
                flask_app.solver_state = {"status": "done"}

        flask_app.run_solve = _mock_run_solve

        app = flask_app.app
        app.config["TESTING"] = True
        yield app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client

