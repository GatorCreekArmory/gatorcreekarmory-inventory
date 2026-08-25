import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GUNBROKER_API = "https://api.gunbroker.com/v1"


def get_access_token():
    dev_key = os.environ.get("GUNBROKER_DEV_KEY")
    username = os.environ.get("GUNBROKER_USERNAME")
    password = os.environ.get("GUNBROKER_PASSWORD")

    if not dev_key or not username or not password:
        return None, "GunBroker credentials are not fully configured."

    response = requests.post(
        f"{GUNBROKER_API}/Users/AccessToken",
        headers={
            "X-DevKey": dev_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "Username": username,
            "Password": password,
        },
        timeout=15,
    )

    if not response.ok:
        return None, f"GunBroker login failed with status {response.status_code}."

    data = response.json()
    return data.get("AccessToken"), None


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "Gator Creek Armory Inventory"
    })


@app.route("/inventory")
def inventory():
    dev_key = os.environ.get("GUNBROKER_DEV_KEY")

    if not dev_key:
        return jsonify({
            "error": "GunBroker DevKey is not configured."
        }), 503

    access_token, error = get_access_token()

    if error:
        return jsonify({"error": error}), 503

    headers = {
        "X-DevKey": dev_key,
        "X-AccessToken": access_token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            f"{GUNBROKER_API}/ItemsSelling",
            headers=headers,
            params={
                "TimeFrame": 0,
                "PageSize": 100
            },
            timeout=15,
        )

        if not response.ok:
            return jsonify({
                "error": "GunBroker inventory request failed.",
                "status": response.status_code
            }), response.status_code

        return jsonify(response.json())

    except requests.RequestException:
        return jsonify({
            "error": "Unable to contact GunBroker."
        }), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
