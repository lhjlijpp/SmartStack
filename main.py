import os
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import uvicorn

app = FastAPI()

templates = Jinja2Templates(directory="templates")

API_KEY = os.getenv("TWELVE_API_KEY")
CACHE_DURATION = 120  # seconds (2 minutes)

# Cache variables
last_fetch_time = 0
cached_prices = []
cached_signal = "HOLD"

def calculate_signal(prices):
    short_term_window = 5
    long_term_window = 20

    if len(prices) < long_term_window:
        return "HOLD"

    short_term_sma = sum(prices[:short_term_window]) / short_term_window
    long_term_sma = sum(prices[:long_term_window]) / long_term_window

    if short_term_sma > long_term_sma:
        return "BUY"
    elif short_term_sma < long_term_sma:
        return "SELL"
    else:
        return "HOLD"

def fetch_data(symbol="EUR/USD", interval="1min"):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if "values" not in data:
        return None

    prices = [float(x['close']) for x in data["values"]]
    return prices

def get_cached_signal(symbol="EUR/USD", interval="1min"):
    global last_fetch_time, cached_prices, cached_signal

    now = time.time()
    if now - last_fetch_time > CACHE_DURATION or not cached_prices:
        prices = fetch_data(symbol, interval)
        if prices is None:
            return None, None

        signal = calculate_signal(prices)
        cached_prices = prices
        cached_signal = signal
        last_fetch_time = now

    return cached_signal, cached_prices

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    symbol = "EUR/USD"
    signal, prices = get_cached_signal(symbol)

    if prices is None:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "signal": "Error",
            "pair": symbol,
            "price": "Unavailable"
        })

    return templates.TemplateResponse("index.html", {
        "request": request,
        "signal": signal,
        "pair": symbol,
        "price": prices[0]
    })

@app.get("/signal")
def get_signal():
    symbol = "EUR/USD"
    signal, prices = get_cached_signal(symbol)

    if prices is None:
        return {"status": "error", "detail": "Could not fetch prices"}

    return {"signal": signal, "data": prices}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
