import os
import sys
import json
from flask import Flask, jsonify, request, abort

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY", "")

def require_api_key():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        abort(401, description="Invalid or missing API key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")

sys.path.insert(0, ROOT_DIR)

os.makedirs(DATA_DIR, exist_ok=True)


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}


@app.route("/solve", methods=["POST"])
def solve():
    require_api_key()
    data = request.get_json(force=True)

    input_path = os.path.join(DATA_DIR, "input.json")
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    from script import solve_pipeline
    solve_pipeline(input_path=input_path, data_dir=DATA_DIR)

    output_path = os.path.join(DATA_DIR, "output.json")
    with open(output_path, encoding="utf-8") as f:
        return jsonify(json.load(f))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
