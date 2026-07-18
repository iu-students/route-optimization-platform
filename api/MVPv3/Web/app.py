# flake8: noqa: E402
import os
import sys

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_MVPv3_DIR = os.path.normpath(os.path.join(_BASE_DIR, ".."))
sys.path.insert(0, _MVPv3_DIR)

import json
import time
import threading
import importlib
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from Web.validator import ValidationError, validate_input
from Shared import history

app = Flask(__name__)
CORS(app)

BASE_DIR = _BASE_DIR
MVPv3_DIR = _MVPv3_DIR
PROJ_ROOT = os.path.normpath(os.path.join(BASE_DIR, "..", "..", ".."))
DATA_DIR = os.path.join(PROJ_ROOT, "data")

os.makedirs(DATA_DIR, exist_ok=True)

INPUTS_DIR = os.path.join(DATA_DIR, "inputs")
OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs")
HISTORY_DB_PATH = os.path.join(DATA_DIR, "history.db")
history.init_db(HISTORY_DB_PATH, INPUTS_DIR, OUTPUTS_DIR)

solver_state = {"status": "idle"}
solver_lock = threading.Lock()

SOLUTION_PATH = os.path.join(DATA_DIR, "output.json")
INPUT_PATH = os.path.join(DATA_DIR, "input.json")

API_KEY = os.environ.get("API_KEY", "")


def require_api_key():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        abort(401, description="Invalid or missing API key")


def run_solve(calculation_id):
    global solver_state
    start_time = time.time()
    try:
        def on_stage(name):
            global solver_state
            with solver_lock:
                solver_state = {"status": "computing", "calculation_id": calculation_id, "stage": name}

        cpsat = importlib.import_module("CP-SAT.main")
        cpsat.solve_pipeline(input_path=INPUT_PATH, output_path=SOLUTION_PATH, on_stage=on_stage)

        with open(SOLUTION_PATH, encoding="utf-8") as f:
            output_data = json.load(f)

        execution_time = time.time() - start_time
        objective_function_cost = output_data.get("statistics", {}).get("total_cost")
        history.finish_success(
            HISTORY_DB_PATH, OUTPUTS_DIR, calculation_id,
            output_data, execution_time, objective_function_cost,
        )

        with solver_lock:
            solver_state = {"status": "done", "calculation_id": calculation_id}
    except Exception as e:
        execution_time = time.time() - start_time
        with solver_lock:
            solver_state = {"status": "error", "calculation_id": calculation_id, "message": str(e)}
        history.finish_error(HISTORY_DB_PATH, OUTPUTS_DIR, calculation_id, str(e), execution_time)


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

    calculation_id = history.start_calculation(HISTORY_DB_PATH, INPUTS_DIR, data)

    with open(INPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    with solver_lock:
        solver_state = {"status": "computing", "calculation_id": calculation_id, "stage": "starting"}

    thread = threading.Thread(target=run_solve, args=(calculation_id,))
    thread.start()

    return jsonify({"status": "started", "calculation_id": calculation_id}), 202


@app.route("/solution", methods=["GET"])
def solution():
    require_api_key()

    with solver_lock:
        status = solver_state.get("status")

    if status == "computing":
        with solver_lock:
            resp = {"status": "computing"}
            if "stage" in solver_state:
                resp["stage"] = solver_state["stage"]
            return jsonify(resp)

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
        with solver_lock:
            resp = {"status": "computing"}
            if "stage" in solver_state:
                resp["stage"] = solver_state["stage"]
            return jsonify(resp)

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


@app.route("/history", methods=["GET"])
def history_list():
    require_api_key()
    return jsonify({"history": history.get_all(HISTORY_DB_PATH)})


@app.route("/history/<int:calculation_id>", methods=["GET"])
def history_detail(calculation_id):
    require_api_key()
    record = history.get_by_id(HISTORY_DB_PATH, calculation_id)
    if record is None:
        return jsonify({"status": "error", "message": "Not found"}), 404
    return jsonify(record)


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=5003, debug=debug)