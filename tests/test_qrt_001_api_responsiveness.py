import time
import json


class TestQRT001ApiResponsiveness:

    def test_health_response_time(self, client):
        start = time.time()
        resp = client.get("/health")
        elapsed = time.time() - start
        assert resp.status_code == 200
        assert elapsed < 2.0, f"GET /health took {elapsed:.3f}s, expected < 2.0s"

    def test_solve_returns_immediately(self, client):
        payload = {
            "depot": {"x": 0, "y": 0, "load_time": 5},
            "orders": [
                {
                    "id": 1, "x": 10, "y": 10, "volume": 5,
                    "time_window": [0, 100], "vehicle_service_time": 5,
                    "loader_cnt": 0, "loader_service_time": 0, "optional": False
                }
            ],
            "weights": {
                "optional_order_penalty": 1000, "vehicle_salary": 500,
                "loader_salary": 300, "fuel_cost": 10, "loader_work": 5
            },
            "vehicle_capacity": 100, "vehicle_speed": 1,
            "loader_speed": 1, "vehicle_shift_size": 480, "loader_shift_size": 480
        }

        headers = {"X-API-Key": "test-api-key-123", "Content-Type": "application/json"}

        start = time.time()
        resp = client.post("/solve", data=json.dumps(payload), headers=headers)
        elapsed = time.time() - start

        assert elapsed < 2.0, f"POST /solve took {elapsed:.3f}s, expected < 2.0s"
        assert resp.status_code in (202,), f"Expected 202, got {resp.status_code}"

    def test_solution_response_time_when_computing(self, client):
        headers = {"X-API-Key": "test-api-key-123"}

        payload = {
            "depot": {"x": 0, "y": 0, "load_time": 5},
            "orders": [
                {
                    "id": 1, "x": 10, "y": 10, "volume": 5,
                    "time_window": [0, 100], "vehicle_service_time": 5,
                    "loader_cnt": 0, "loader_service_time": 0, "optional": False
                }
            ],
            "weights": {
                "optional_order_penalty": 1000, "vehicle_salary": 500,
                "loader_salary": 300, "fuel_cost": 10, "loader_work": 5
            },
            "vehicle_capacity": 100, "vehicle_speed": 1,
            "loader_speed": 1, "vehicle_shift_size": 480, "loader_shift_size": 480
        }

        import importlib
        flask_app = importlib.import_module("app")
        flask_app.solver_state = {"status": "computing"}

        start = time.time()
        resp = client.get("/solution", headers=headers)
        elapsed = time.time() - start

        assert elapsed < 2.0, f"GET /solution (computing) took {elapsed:.3f}s, expected < 2.0s"
        assert resp.status_code == 200
        assert resp.get_json().get("status") == "computing"
