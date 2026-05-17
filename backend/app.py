import logging

from flask import Flask, jsonify
from flask_cors import CORS

from config import PORT
from routes.people import bp as people_bp
from routes.runs import bp as runs_bp
from routes.sms import bp as sms_bp
from routes.agentphone_webhook import bp as webhook_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = Flask(__name__)
CORS(app)

app.register_blueprint(people_bp)
app.register_blueprint(runs_bp)
app.register_blueprint(sms_bp)
app.register_blueprint(webhook_bp)


@app.get("/")
def index():
    return jsonify({"service": "artificial-people", "ok": True})


@app.get("/health")
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=True)
