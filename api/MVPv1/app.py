import os
import sys
import json
import threading
from flask import Flask, jsonify, request, abort
from flask_cors import CORS

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

solver_state = {"status": "idle"}
solver_lock = threading.Lock()

SOLUTION_PATH = os.path.join(DATA_DIR, "output.json")
INPUT_PATH = os.path.join(DATA_DIR, "input.json")


def run_solve():
    global solver_state
    try:
        from script import solve_pipeline
        solve_pipeline(input_path=INPUT_PATH, data_dir=DATA_DIR)
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
