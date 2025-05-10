from fastapi import FastAPI
import requests
import os
import uvicorn

app = FastAPI()

# Get API key from environment variable
API_KEY = os.getenv("API_KEY")  # Ensure the API key is properly set as an environment variable

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}

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

# Ensure the app listens on the correct port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Use the PORT environment variable, default to 8000 if not set
    uvicorn.run(app, host="0.0.0.0", port=port)  # Bind to 0.0.0.0 and the correct port
