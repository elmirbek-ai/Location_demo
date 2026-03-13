from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from weather_service import get_weather
from recommendation import recommend

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/")
def home(request: Request):

    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.post("/location")
async def receive_location(data: dict):

    lat = data.get("lat")
    lon = data.get("lon")

    weather = get_weather(lat, lon)

    recommendation = recommend(weather)

    return JSONResponse({
        "weather": weather,
        "recommendation": recommendation
    })