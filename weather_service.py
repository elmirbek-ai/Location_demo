import requests
from config import API_KEY


def get_weather(lat, lon):

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    )

    try:

        response = requests.get(url, timeout=5)

        data = response.json()

        if "main" not in data:
            return {
                "temperature": None,
                "humidity": None,
                "error": data
            }

        weather = {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "city": data.get("name")
        }

        return weather

    except Exception as e:

        return {
            "temperature": None,
            "humidity": None,
            "error": str(e)
        }