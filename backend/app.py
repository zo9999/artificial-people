from flask import Flask, jsonify
from flask_cors import CORS

from config import PORT
from routes.people import bp as people_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(people_bp)


@app.get("/")
def index():
    return jsonify({"service": "artificial-people", "ok": True})


@app.get("/health")
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
