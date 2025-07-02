from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import requests
import random
import locale

load_dotenv()

app = Flask(__name__)

# Set locale for number formatting
locale.setlocale(locale.LC_ALL, "")

# API endpoints from environment variables (do not expose defaults)
CAT_API_URL = os.getenv("CAT_API_URL")
COUNTRY_API_URL = os.getenv("COUNTRY_API_URL")
COINGECKO_LIST_URL = os.getenv("COINGECKO_LIST_URL")
COINGECKO_COIN_URL = os.getenv("COINGECKO_COIN_URL")


# Custom filter for formatting large numbers
@app.template_filter("format")
def format_number(value):
    try:
        return locale.format_string("%d", value, grouping=True)
    except (ValueError, TypeError):
        return value


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
        user_input = request.form["coin"].lower()

        # CoinGecko wants coin IDs like 'bitcoin', not symbols like 'btc'
        # So we get the full list of coins to find the match
        list_url = COINGECKO_LIST_URL
        list_response = requests.get(list_url)
        coin_list = list_response.json()

        # Try to match user input to ID or symbol
        match = next(
            (
                c
                for c in coin_list
                if c["id"] == user_input or c["symbol"] == user_input
            ),
            None,
        )

        if match:
            coin_id = match["id"]
            coin_url = f"{COINGECKO_COIN_URL}{coin_id}"
            coin_response = requests.get(coin_url)
            if coin_response.status_code == 200:
                coin_data = coin_response.json()
            else:
                error = "Couldn't fetch coin data."
        else:
            error = "Coin not found. Try full name like 'bitcoin' or symbol like 'btc'."

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
