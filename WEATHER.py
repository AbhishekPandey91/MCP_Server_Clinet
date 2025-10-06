# WEATHER.py
import os
import requests
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

mcp = FastMCP("Weather_Server")

@mcp.tool()
def get_weather(city: str) -> str:
    """
    Returns the current weather for a given city using OpenWeatherMap API.
    Example: get_weather("Delhi")
    """
    if not OPENWEATHER_API_KEY:
        return "Error: OPENWEATHER_API_KEY not set in environment."

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if response.status_code != 200:
            return f"Error fetching weather: {data.get('message', 'Unknown error')}"

        city_name = data["name"]
        temp = data["main"]["temp"]
        condition = data["weather"][0]["description"].capitalize()
        humidity = data["main"]["humidity"]

        return f"Weather in {city_name}: {condition}, {temp}°C, Humidity {humidity}%"

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")

