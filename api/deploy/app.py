from flask import Flask, jsonify, request, abort
import json
import os

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY", "")

with open("response.json") as f:
    response_data = json.load(f)


@app.route("/solve", methods=["POST"])
def solve():
    key = request.headers.get("X-API-Key")
    if not key or key != API_KEY:
        abort(401, description="Invalid or missing API key")
    data = request.get_json(force=True)
    return jsonify(response_data)


if __name__ == "__main__":
    app.run(app.run(host="0.0.0.0", port=5000, debug=True))
