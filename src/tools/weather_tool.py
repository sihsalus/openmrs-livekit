"""Tool: Clima actual via Open-Meteo (geocoding + forecast)"""
import aiohttp
from livekit.agents import RunContext, function_tool

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

_WMO_DESCRIPTIONS = {
    0: "despejado",
    1: "mayormente despejado",
    2: "parcialmente nublado",
    3: "nublado",
    45: "niebla",
    48: "niebla con escarcha",
    51: "llovizna ligera",
    53: "llovizna moderada",
    55: "llovizna intensa",
    61: "lluvia ligera",
    63: "lluvia moderada",
    65: "lluvia intensa",
    71: "nieve ligera",
    73: "nieve moderada",
    75: "nieve intensa",
    80: "chubascos ligeros",
    81: "chubascos moderados",
    82: "chubascos intensos",
    95: "tormenta eléctrica",
    96: "tormenta con granizo ligero",
    99: "tormenta con granizo fuerte",
}


@function_tool(
    name="get_weather",
    description="Get the current weather for a city. Use when the user asks about the weather.",
)
async def get_weather(
    context: RunContext,
    city: str,
) -> str:
    """Look up current weather for a given city.

    Args:
        city: The city name to check weather for, e.g. 'Bogota' or 'Madrid'.
    """
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Step 1: Geocode city name to coordinates
            async with session.get(_GEOCODE_URL, params={"name": city, "count": 1, "language": "es"}) as resp:
                if resp.status != 200:
                    return f"No pude encontrar la ubicación de {city}."
                geo = await resp.json()

            results = geo.get("results")
            if not results:
                return f"No encontré la ciudad {city}."

            lat = results[0]["latitude"]
            lon = results[0]["longitude"]
            resolved_name = results[0].get("name", city)

            # Step 2: Get current weather
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "timezone": "auto",
            }
            async with session.get(_WEATHER_URL, params=params) as resp:
                if resp.status != 200:
                    return f"No pude consultar el clima para {city}."
                weather = await resp.json()

        current = weather["current"]
        temp = current["temperature_2m"]
        humidity = current["relative_humidity_2m"]
        code = current["weather_code"]
        wind = current["wind_speed_10m"]
        desc = _WMO_DESCRIPTIONS.get(code, "condiciones variables")

        return (
            f"En {resolved_name} ahora: {desc}, temperatura {temp} grados celsius, "
            f"humedad {humidity} por ciento, viento a {wind} kilómetros por hora."
        )
    except Exception:
        return f"No pude consultar el clima para {city} en este momento."
