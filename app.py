import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GUNBROKER_API = "https://api.gunbroker.com/v1"

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "Gator Creek Armory Inventory"
    })

@app.route("/inventory")
def inventory():
    dev_key = os.environ.get("GUNBROKER_DEV_KEY")
    access_token = os.environ.get("GUNBROKER_ACCESS_TOKEN")

    if not dev_key or not access_token:
        return jsonify({
            "error": "GunBroker API credentials have not been configured yet."
        }), 503

    headers = {
        "X-DevKey": dev_key,
        "X-AccessToken": access_token,
        "Accept": "application/json"
    }

    try:
        response = requests.get(
            f"{GUNBROKER_API}/ItemsSelling",
            headers=headers,
            timeout=15
        )

        if not response.ok:
            return jsonify({
                "error": "GunBroker API request failed.",
                "status": response.status_code
            }), response.status_code

        return jsonify(response.json())

    except requests.RequestException as exc:
        return jsonify({
            "error": "Unable to contact GunBroker."
        }), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
