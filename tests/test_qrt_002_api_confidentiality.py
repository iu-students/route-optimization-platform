import json


class TestQRT002ApiConfidentiality:

    def test_solve_without_api_key_returns_401(self, client):
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

        resp = client.post("/solve", data=json.dumps(payload), content_type="application/json")
        assert resp.status_code == 401, f"Expected 401 without API key, got {resp.status_code}"

    def test_solution_without_api_key_returns_401(self, client):
        resp = client.get("/solution")
        assert resp.status_code == 401, f"Expected 401 without API key, got {resp.status_code}"

    def test_solve_with_invalid_api_key_returns_401(self, client):
        headers = {"X-API-Key": "wrong-key-999"}
        resp = client.post("/solve", headers=headers)
        assert resp.status_code == 401, f"Expected 401 with wrong key, got {resp.status_code}"

    def test_solution_with_invalid_api_key_returns_401(self, client):
        headers = {"X-API-Key": "wrong-key-999"}
        resp = client.get("/solution", headers=headers)
        assert resp.status_code == 401, f"Expected 401 with wrong key, got {resp.status_code}"

    def test_health_without_api_key_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200, f"Expected 200 for /health without key, got {resp.status_code}"

    def test_solve_with_valid_api_key_returns_not_401(self, client):
        headers = {"X-API-Key": "test-api-key-123", "Content-Type": "application/json"}
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

        resp = client.post("/solve", data=json.dumps(payload), headers=headers)
        assert resp.status_code != 401, f"Expected non-401 with valid key, got {resp.status_code}"

    def test_solution_with_valid_api_key_returns_not_401(self, client):
        headers = {"X-API-Key": "test-api-key-123"}
        resp = client.get("/solution", headers=headers)
        assert resp.status_code != 401, f"Expected non-401 with valid key, got {resp.status_code}"

    def test_error_response_does_not_leak_api_key(self, client):
        headers = {"X-API-Key": "test-api-key-123", "Content-Type": "application/json"}
        resp = client.post("/solve", data="not-json", headers=headers)
        body = resp.get_data(as_text=True).lower()
        assert "test-api-key-123" not in body, "Error response leaked the API key"
