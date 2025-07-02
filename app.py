from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import requests
import random
import time

load_dotenv()

app = Flask(__name__)

# API endpoints
CAT_API_URL = os.getenv("CAT_API_URL")
COUNTRY_API_URL = os.getenv("COUNTRY_API_URL")
COINGECKO_LIST_URL = os.getenv("COINGECKO_LIST_URL")
COINGECKO_COIN_URL = os.getenv("COINGECKO_COIN_URL")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

# Coin list cache for CoinGecko
coin_list_cache = {"data": None, "timestamp": 0}
COIN_LIST_CACHE_TTL = 600  # 10 minutos


def get_coin_list():
    now = time.time()
    headers = {"accept": "application/json", "x-cg-pro-api-key": COINGECKO_API_KEY}
    # print("CoinGecko headers:", headers)
    if (
        coin_list_cache["data"] is None
        or now - coin_list_cache["timestamp"] > COIN_LIST_CACHE_TTL
    ):
        response = requests.get(COINGECKO_LIST_URL, headers=headers)
        # print("CoinGecko /coins/list status:", response.status_code, response.text)
        response.raise_for_status()
        coin_list_cache["data"] = response.json()
        coin_list_cache["timestamp"] = now
    return coin_list_cache["data"]


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html", active_page="home")


@app.route("/api", methods=["GET", "POST"])
def api():
    # API GATOS
    try:
        response = requests.get(CAT_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        cat_url = data[0]["url"] if data and "url" in data[0] else ""
    except Exception:
        cat_url = ""

    # API PAÍSES
    try:
        response = requests.get(COUNTRY_API_URL, timeout=5)
        response.raise_for_status()
        countries = response.json()
        country = random.choice(countries) if countries else {}
    except Exception:
        country = {}

    # Extraer datos del país
    country_info = {
        "name": country.get("name", {}).get("common", "Unknown"),
        "flag": country.get("flags", {}).get("png", ""),
        "capital": country.get("capital", ["Unknown"])[0]
        if country.get("capital")
        else "Unknown",
        "region": country.get("region", "Unknown"),
        "population": country.get("population", "Unknown"),
    }

    # API CRIPTOMONEDAS
    coin_data = None
    error = None

    if request.method == "POST":
        user_input = request.form["coin"].strip().lower()
        try:
            coin_list = get_coin_list()
            # Buscar por id o symbol (case-insensitive)
            match = next(
                (
                    c
                    for c in coin_list
                    if c["id"].lower() == user_input
                    or c["symbol"].lower() == user_input
                ),
                None,
            )
            if match:
                coin_id = match["id"]
                coin_url = f"{COINGECKO_COIN_URL}{coin_id}"
                headers = (
                    {"x-cg-pro-api-key": COINGECKO_API_KEY} if COINGECKO_API_KEY else {}
                )

                coin_response = requests.get(coin_url, headers=headers, timeout=8)
                coin_response.raise_for_status()
                coin_data = coin_response.json()
            else:
                error = "Coin no encontrado."
        except Exception as e:
            error = f"Error adquiriendo datos de coin: {str(e)}"

    return render_template(
        "api.html",
        active_page="API",
        cat_url=cat_url,
        country=country_info,
        coin=coin_data,
        error=error,
    )


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")


@app.route("/documentacion")
def documentacion():
    return render_template("documentacion.html", active_page="documentacion")


if __name__ == "__main__":
    app.run(debug=True)
