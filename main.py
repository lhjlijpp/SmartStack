from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import os
import uvicorn

app = FastAPI()

# Set up templates folder for HTML
templates = Jinja2Templates(directory="templates")

# Get API key from environment variable
API_KEY = os.getenv("TWELVE_API_KEY")  # Ensure the API key is properly set in Render

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Example hardcoded values for now – we’ll make dynamic later
    return templates.TemplateResponse("index.html", {
        "request": request,
        "signal": "SELL",
        "pair": "USD/EUR",
        "price": 1.1245
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

    prices = [float(x['close']) for x in data["values"][:2]]
    signal = "BUY" if prices[0] > prices[1] else "SELL"

    return {"signal": signal, "data": prices}

# Ensure the app listens on the correct port when running locally
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Use the PORT environment variable, default to 8000 if not set
    uvicorn.run(app, host="0.0.0.0", port=port)
