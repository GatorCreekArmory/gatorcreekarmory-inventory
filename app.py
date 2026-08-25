import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GUNBROKER_API = "https://api.gunbroker.com/v1"
USER_AGENT = "GatorCreekArmory/GatorCreekArmory/1.0/InventorySync"

_cached_token = None


def get_access_token():
    global _cached_token

    if _cached_token:
        return _cached_token

    dev_key = os.environ.get("GUNBROKER_DEV_KEY")
    username = os.environ.get("GUNBROKER_USERNAME")
    password = os.environ.get("GUNBROKER_PASSWORD")

    if not dev_key or not username or not password:
        raise RuntimeError("GunBroker credentials are not configured.")

    response = requests.post(
        f"{GUNBROKER_API}/Users/AccessToken",
        headers={
            "X-DevKey": dev_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT
        },
        json={
            "Username": username,
            "Password": password
        },
        timeout=15
    )

    if not response.ok:
        raise RuntimeError(
            f"GunBroker login failed with status {response.status_code}."
        )

    data = response.json()

    if "accessToken" not in data:
        raise RuntimeError("GunBroker did not return an access token.")

    _cached_token = data["accessToken"]
    return _cached_token


def get_selling_items():
    global _cached_token

    dev_key = os.environ.get("GUNBROKER_DEV_KEY")
    token = get_access_token()

    headers = {
        "X-DevKey": dev_key,
        "X-AccessToken": token,
        "Accept": "application/json",
        "User-Agent": USER_AGENT
    }

    response = requests.get(
        f"{GUNBROKER_API}/ItemsSelling",
        headers=headers,
        timeout=15
    )

    if response.status_code == 401:
        _cached_token = None
        token = get_access_token()
        headers["X-AccessToken"] = token

        response = requests.get(
            f"{GUNBROKER_API}/ItemsSelling",
            headers=headers,
            timeout=15
        )

    return response


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "Gator Creek Armory Inventory",
        "environment": "production"
    })


@app.route("/inventory")
def inventory():
    try:
        response = get_selling_items()

        if not response.ok:
            return jsonify({
                "error": "GunBroker API request failed.",
                "status": response.status_code
            }), response.status_code

        data = response.json()
        cleaned = []

        for item in data.get("results", []):
            item_id = item.get("itemID")

            price = (
                item.get("buyNowPrice")
                or item.get("fixedPrice")
                or item.get("currentBid")
                or item.get("startingBid")
                or item.get("minimumBid")
                or 0
            )

            cleaned.append({
                "id": item_id,
                "title": item.get("title", "GunBroker Listing"),
                "price": price,
                "image": item.get("thumbnailURL", ""),
                "url": f"https://www.gunbroker.com/item/{item_id}",
                "watchers": item.get("watchersCount", 0)
            })

        return jsonify({
            "count": len(cleaned),
            "items": cleaned
        })

    except requests.RequestException as exc:
        return jsonify({
            "error": "Unable to contact GunBroker.",
            "details": str(exc)
        }), 502

    except Exception as exc:
        return jsonify({
            "error": str(exc)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
