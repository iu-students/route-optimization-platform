# flake8: noqa: E402
import os
import sys

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_MVPv2_DIR = os.path.normpath(os.path.join(_BASE_DIR, ".."))
sys.path.insert(0, _MVPv2_DIR)

import json
import threading
import importlib
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from Web.validator import ValidationError, validate_input

app = Flask(__name__)
CORS(app)

BASE_DIR = _BASE_DIR
MVPv2_DIR = _MVPv2_DIR
PROJ_ROOT = os.path.normpath(os.path.join(BASE_DIR, "..", "..", ".."))
DATA_DIR = os.path.join(PROJ_ROOT, "data")

os.makedirs(DATA_DIR, exist_ok=True)

solver_state = {"status": "idle"}
solver_lock = threading.Lock()

SOLUTION_PATH = os.path.join(DATA_DIR, "output.json")
INPUT_PATH = os.path.join(DATA_DIR, "input.json")

API_KEY = os.environ.get("API_KEY", "")


def require_api_key():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        abort(401, description="Invalid or missing API key")


def run_solve():
    global solver_state
    try:
        cpsat = importlib.import_module("CP-SAT.main")
        cpsat.solve_pipeline(input_path=INPUT_PATH, output_path=SOLUTION_PATH)
        with solver_lock:
            solver_state = {"status": "done"}
    except Exception as e:
        with solver_lock:
            solver_state = {"status": "error", "message": str(e)}


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}


@app.route("/solve", methods=["POST"])
def solve():
    global solver_state
    require_api_key()

    with solver_lock:
        if solver_state.get("status") == "computing":
            return jsonify({"status": "computing",
                            "message": "Already solving"}), 409

    data = request.get_json(force=True)

    try:
        validate_input(data)
    except ValidationError as e:
        return jsonify({"status": "error", "errors": e.errors}), 400

    with open(INPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    with solver_lock:
        solver_state = {"status": "computing"}

    thread = threading.Thread(target=run_solve)
    thread.start()

    return jsonify({"status": "started"}), 202


@app.route("/solution", methods=["GET"])
def solution():
    require_api_key()

    with solver_lock:
        status = solver_state.get("status")

    if status == "computing":
        return jsonify({"status": "computing"})

    if status == "error":
        with solver_lock:
            return jsonify(solver_state), 500

    if os.path.exists(SOLUTION_PATH):
        with open(SOLUTION_PATH, encoding="utf-8") as f:
            return jsonify({"status": "done", "solution": json.load(f)})

    return jsonify({"status": "idle", "message": "No computation started yet"})


@app.route("/validate", methods=["POST"])
def validate():
    data = request.get_json(force=True)
    try:
        result = validate_input(data)
        return jsonify(result)
    except ValidationError as e:
        return jsonify({"status": "error", "errors": e.errors}), 400


@app.route("/metrics", methods=["GET"])
def metrics():
    require_api_key()

    with solver_lock:
        status = solver_state.get("status")

    if status == "computing":
        return jsonify({"status": "computing"})

    if status == "error":
        with solver_lock:
            return jsonify(solver_state), 500

    if os.path.exists(SOLUTION_PATH):
        with open(SOLUTION_PATH, encoding="utf-8") as f:
            sol = json.load(f)
        stats = sol.get("statistics", {})
        return jsonify({
            "status": "done",
            "metrics": {
                "total_cost": stats.get("total_cost", 0),
                "fuel_cost": stats.get("fuel_cost", 0),
                "vehicle_salaries": stats.get("vehicle_salaries", 0),
                "loader_salaries": stats.get("loader_salaries", 0),
                "loader_work_cost": stats.get("loader_work_cost", 0),
                "penalties": stats.get("penalties", 0),
                "vehicles_used": len(sol.get("vehicles", [])),
                "loaders_used": len(sol.get("loaders", [])),
            }
        })

    return jsonify({"status": "idle", "message": "No computation started yet"})


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=5002, debug=debug)
