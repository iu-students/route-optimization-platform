from flask import Flask, jsonify, request, abort, Response
import json
import os

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY", "")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_DIR = os.path.normpath(os.path.join(BASE_DIR, ".."))

with open(os.path.join(BASE_DIR, "response.json")) as f:
    response_data = json.load(f)

with open(os.path.join(BASE_DIR, "swagger.html")) as f:
    swagger_html = f.read()

with open(os.path.join(API_DIR, "openapi.yaml")) as f:
    openapi_yaml = f.read()


@app.route("/solve", methods=["POST"])
def solve():
    key = request.headers.get("X-API-Key")
    if not key or key != API_KEY:
        abort(401, description="Invalid or missing API key")
    data = request.get_json(force=True)
    return jsonify(response_data)


@app.route("/docs/")
def swagger_ui():
    return swagger_html


@app.route("/openapi.yaml")
def openapi_spec():
    return Response(openapi_yaml, mimetype="text/yaml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
