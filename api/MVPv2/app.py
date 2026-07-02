import os
import sys
import json
import time
import threading
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from validator import ValidationError, validate_input

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("API_KEY", "")


def require_api_key():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        abort(401, description="Invalid or missing API key")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")

sys.path.insert(0, ROOT_DIR)

os.makedirs(DATA_DIR, exist_ok=True)

SOLVER_MAX_TIME = 120

solver_state = {"status": "idle"}
solver_lock = threading.Lock()

SOLUTION_PATH = os.path.join(DATA_DIR, "output.json")
STATISTICS_PATH = os.path.join(DATA_DIR, "statistics.json")
INPUT_PATH = os.path.join(DATA_DIR, "input.json")


def run_solve():
    global solver_state
    try:
        from script import solve_pipeline
        solve_pipeline(input_path=INPUT_PATH, data_dir=DATA_DIR)
        stats = None
        if os.path.exists(STATISTICS_PATH):
            with open(STATISTICS_PATH, encoding="utf-8") as f:
                stats = json.load(f)
        with solver_lock:
            solver_state = {"status": "done", "statistics": stats}
    except Exception as e:
        with solver_lock:
            solver_state = {"status": "error", "message": str(e)}


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}


@app.route("/validation", methods=["POST"])
def validation():
    require_api_key()
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({
            "status": "error",
            "errors": [{"path": "", "message": "Invalid JSON"}]
        }), 400
    try:
        validate_input(data)
        return jsonify({"status": "ok"})
    except ValidationError as e:
        return jsonify({"status": "error", "errors": e.errors}), 400


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
        solver_state = {"status": "computing", "start_time": time.time(), "max_time": SOLVER_MAX_TIME}

    thread = threading.Thread(target=run_solve)
    thread.start()

    return jsonify({"status": "started"}), 202


def _computing_response():
    with solver_lock:
        start = solver_state.get("start_time")
        max_t = solver_state.get("max_time", SOLVER_MAX_TIME)
    elapsed = time.time() - start if start else 0
    remaining = max(0, round(max_t - elapsed))
    return jsonify({"status": "computing", "remaining_time_seconds": remaining})


@app.route("/solution", methods=["GET"])
def solution():
    require_api_key()

    with solver_lock:
        status = solver_state.get("status")

    if status == "computing":
        return _computing_response()

    if status == "error":
        with solver_lock:
            return jsonify(solver_state), 500

    if os.path.exists(SOLUTION_PATH):
        with open(SOLUTION_PATH, encoding="utf-8") as f:
            return jsonify({"status": "done", "solution": json.load(f)})

    return jsonify({"status": "idle", "message": "No computation started yet"})


@app.route("/metrics", methods=["GET"])
def metrics():
    require_api_key()

    with solver_lock:
        status = solver_state.get("status")

    if status == "computing":
        return _computing_response()

    if status == "error":
        with solver_lock:
            return jsonify(solver_state), 500

    if status == "done":
        stats = solver_state.get("statistics")
        if stats:
            return jsonify({"status": "done", "statistics": stats})
        if os.path.exists(STATISTICS_PATH):
            with open(STATISTICS_PATH, encoding="utf-8") as f:
                return jsonify({"status": "done", "statistics": json.load(f)})

    return jsonify({"status": "idle", "message": "No computation started yet"})


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=5002, debug=debug)
