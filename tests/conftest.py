import pytest
import os
import sys
import json
import tempfile

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

TEST_TARGET = os.environ.get("TEST_TARGET", "v3")

for p in [
    os.path.join(PROJECT_ROOT, "api", "MVPv3"),
    os.path.join(PROJECT_ROOT, "api", "MVPv3", "CP-SAT"),
    os.path.join(PROJECT_ROOT, "api", "MVPv3", "Shared"),
    os.path.join(PROJECT_ROOT, "api", "MVPv3", "Web"),
]:
    if p not in sys.path:
        sys.path.append(p)

from Shared.models import Scenario, Depot, Weights, Order

from vehicle_routes import set_shift_mode
set_shift_mode("earliest")


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
        import importlib
        flask_app = importlib.import_module("app")

        flask_app.API_KEY = TEST_API_KEY
        flask_app.DATA_DIR = tmpdir
        flask_app.INPUT_PATH = os.path.join(tmpdir, "input.json")
        flask_app.SOLUTION_PATH = os.path.join(tmpdir, "output.json")
        flask_app.INPUTS_DIR = os.path.join(tmpdir, "inputs")
        flask_app.OUTPUTS_DIR = os.path.join(tmpdir, "outputs")
        flask_app.HISTORY_DB_PATH = os.path.join(tmpdir, "history.db")
        flask_app.solver_state = {"status": "idle"}

        os.makedirs(flask_app.INPUTS_DIR, exist_ok=True)
        os.makedirs(flask_app.OUTPUTS_DIR, exist_ok=True)

        from Shared.history import init_db
        init_db(flask_app.HISTORY_DB_PATH, flask_app.INPUTS_DIR, flask_app.OUTPUTS_DIR)

        def _mock_run_solve(calculation_id):
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
