import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from datetime import datetime, timedelta
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

API_KEY = os.getenv("TWELVE_API_KEY")  # Your Twelve Data API key

# Strategy: Simple Moving Average (SMA) Crossover
def calculate_signal(prices):
    short_term_window = 5
    long_term_window = 20

    if len(prices) < long_term_window:
        return "HOLD"

    short_sma = sum(prices[:short_term_window]) / short_term_window
    long_sma = sum(prices[:long_term_window]) / long_term_window

    if short_sma > long_sma:
        return "BUY"
    elif short_sma < long_sma:
        return "SELL"
    else:
        return "HOLD"

# Fetch data with timestamp freshness check
def fetch_prices(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&apikey={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if "values" not in data:
            return None

        latest_timestamp = data["values"][0]["datetime"]
        latest_time = datetime.strptime(latest_timestamp, "%Y-%m-%d %H:%M:%S")

        # Check if data is older than 5 minutes
        if datetime.utcnow() - latest_time > timedelta(minutes=5):
            return None

        prices = [float(x['close']) for x in data["values"][:20]]
        return prices
    except Exception:
        return None

# Shared logic to determine symbol and get signal
def get_valid_signal():
    for symbol in ["EUR/USD", "BTC/USD"]:
        prices = fetch_prices(symbol)
        if prices:
            signal = calculate_signal(prices)
            return signal, symbol, prices
    return "Error", "Unavailable", []

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    signal, symbol, prices = get_valid_signal()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "signal": signal,
        "pair": symbol,
        "price": prices[0] if prices else "Unavailable"
    })

@app.get("/signal")
def get_signal():
    signal, symbol, prices = get_valid_signal()
    return {
        "signal": signal,
        "pair": symbol,
        "data": prices
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
