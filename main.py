import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import uvicorn
import time

app = FastAPI()
templates = Jinja2Templates(directory="templates")

API_KEY = os.getenv("TWELVE_API_KEY")

# In-memory cache
cache = {
    "timestamp": 0,
    "signal": "HOLD",
    "price": "Unavailable",
    "prices": []
}

# SMA Strategy
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

# API call with caching every 2 minutes
def fetch_and_cache_data():
    now = time.time()
    if now - cache["timestamp"] < 120:
        return  # Use cached data

    url = f"https://api.twelvedata.com/time_series?symbol=EUR/USD&interval=1min&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "values" in data:
        prices = [float(x['close']) for x in data["values"][:20]]
        cache["prices"] = prices
        cache["signal"] = calculate_signal(prices)
        cache["price"] = prices[0] if prices else "Unavailable"
        cache["timestamp"] = now

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    fetch_and_cache_data()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "signal": cache["signal"],
        "pair": "EUR/USD",
        "price": cache["price"]
    })

@app.get("/signal")
def get_signal():
    fetch_and_cache_data()
    return {"signal": cache["signal"], "data": cache["prices"]}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
