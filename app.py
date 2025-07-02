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
        user_input = request.form["coin"].strip().lower()
        try:
            list_response = requests.get(COINGECKO_LIST_URL, timeout=8)
            list_response.raise_for_status()
            coin_list = list_response.json()
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
                coin_response = requests.get(coin_url, timeout=8)
                coin_response.raise_for_status()
                coin_data = coin_response.json()
            else:
                error = (
                    "Coin not found. Try full name like 'bitcoin' or symbol like 'btc'."
                )
        except Exception as e:
            error = f"Error fetching coin data: {str(e)}"

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
