from fastapi import FastAPI
import requests
import os

app = FastAPI()

# Get API key from environment variable
API_KEY = os.getenv("307e3dc7c3a7470791e495e03c4a5c88")

@app.get("/signal")
def get_signal():
    symbol = "EUR/USD"
    interval = "1min"
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&apikey={API_KEY}"
    
    response = requests.get(url)
    data = response.json()

    if "values" not in data:
        return {"status": "error", "detail": data}

    prices = [float(x['close']) for x in data["values"][:2]]
    signal = "BUY" if prices[0] > prices[1] else "SELL"

    return {"signal": signal, "data": prices}