import os
import time
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

API_KEY = os.getenv("TWELVE_API_KEY")

# Cache
cache = {
    "timestamp": 0,
    "signal": "HOLD",
    "price": "Unavailable",
    "prices": [],
    "pair": "EUR/USD"
}

def calculate_signal(prices):
    short = 5
    long = 20
    if len(prices) < long:
        return "HOLD"
    short_avg = sum(prices[:short]) / short
    long_avg = sum(prices[:long]) / long
    if short_avg > long_avg:
        return "BUY"
    elif short_avg < long_avg:
        return "SELL"
    return "HOLD"

def fetch_prices(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&apikey={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if "values" in data:
            prices = [float(x['close']) for x in data["values"][:20]]
            return prices
    except Exception:
        pass
    return None

def fetch_and_cache_data():
    now = time.time()
    if now - cache["timestamp"] < 120:
        return

    # Try EUR/USD
    prices = fetch_prices("EUR/USD")
    pair = "EUR/USD"

    # Fallback to BTC/USD if EUR/USD is closed
    if not prices:
        prices = fetch_prices("BTC/USD")
        pair = "BTC/USD"

    if prices:
        cache["prices"] = prices
        cache["signal"] = calculate_signal(prices)
        cache["price"] = prices[0]
        cache["timestamp"] = now
        cache["pair"] = pair
    else:
        cache["signal"] = "Error"
        cache["price"] = "Unavailable"
        cache["pair"] = "Unavailable"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    fetch_and_cache_data()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "signal": cache["signal"],
        "pair": cache["pair"],
        "price": cache["price"]
    })

@app.get("/signal")
def get_signal():
    fetch_and_cache_data()
    return {
        "signal": cache["signal"],
        "pair": cache["pair"],
        "data": cache["prices"]
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
