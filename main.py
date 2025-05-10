import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import uvicorn
from time import sleep

app = FastAPI()

# Set up templates folder for HTML
templates = Jinja2Templates(directory="templates")

# Get API key from environment variable
API_KEY = os.getenv("TWELVE_API_KEY")  # Make sure it's set in Render

# Define the strategy: Simple Moving Average (SMA) Crossover
def calculate_signal(prices):
    short_term_window = 5  # Short-term period (5-min moving average)
    long_term_window = 20  # Long-term period (20-min moving average)

    if len(prices) < long_term_window:
        return "HOLD"  # Not enough data for signal

    # Calculate short-term and long-term moving averages
    short_term_sma = sum(prices[:short_term_window]) / short_term_window
    long_term_sma = sum(prices[:long_term_window]) / long_term_window

    if short_term_sma > long_term_sma:
        return "BUY"
    elif short_term_sma < long_term_sma:
        return "SELL"
    else:
        return "HOLD"

# Fetch live data from Twelve Data API
def fetch_data(symbol="EUR/USD", interval="1min"):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if "values" not in data:
        return None  # Error fetching data

    prices = [float(x['close']) for x in data["values"]]
    return prices

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    symbol = "EUR/USD"
    interval = "1min"
    
    # Fetch the data
    prices = fetch_data(symbol, interval)
    if prices is None:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "signal": "Error",
            "pair": symbol,
            "price": "Unavailable"
        })

    # Calculate the signal based on SMA crossover
    signal = calculate_signal(prices)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "signal": signal,
        "pair": symbol,
        "price": prices[0]  # Latest price
    })

@app.get("/signal")
def get_signal():
    symbol = "EUR/USD"
    interval = "1min"
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&apikey={API_KEY}"

    response = requests.get(url)
    data = response.json()

    if "values" not in data:
        return {"status": "error", "detail": data}

    # Get the last 20 prices for the SMA calculation
    prices = [float(x['close']) for x in data["values"][:20]]
    signal = calculate_signal(prices)

    return {"signal": signal, "data": prices}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
