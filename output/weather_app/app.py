Your final answer must be the great and the most complete as possible, it must be outcome described.")

from typing import Any, Dict
import os
import gradio as gr
from Weather import Weather


def fetch_weather(api_key: str, city: str, units: str) -> str:
    """
    Simple wrapper to use the Weather backend and return a human-readable string.
    """
    api_key = (api_key or "").strip() or os.environ.get("OPENWEATHER_API_KEY", "").strip()
    city = (city or "").strip()

    if not api_key:
        return "Error: No API key provided. Enter an OpenWeatherMap API key or set OPENWEATHER_API_KEY."

    if not city:
        return "Error: Please enter a city name."

    try:
        client = Weather(api_key=api_key)
    except ValueError as e:
        return f"Error creating Weather client: {e}"

    try:
        result: Dict[str, Any] = client.get_weather_by_city(city, units=units)
    except ValueError as e:
        return f"Input error: {e}"
    except ConnectionError as e:
        return f"Connection/API error: {e}"
    except KeyError as e:
        return f"Parsing error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

    # Format the result nicely
    temp = result.get("temperature")
    humidity = result.get("humidity")
    desc = result.get("description", "").capitalize()
    city_name = result.get("city", city)

    unit_symbol = "°C" if units == "metric" else ("°F" if units == "imperial" else "K")

    lines = [
        f"Weather for {city_name}:",
        f"  Condition : {desc or 'N/A'}",
        f"  Temperature: {temp} {unit_symbol}",
        f"  Humidity   : {humidity}%",
    ]
    return "\n".join(lines)


# Build a very simple Gradio UI
def build_interface():
    iface = gr.Interface(
        fn=fetch_weather,
        inputs=[
            gr.Textbox(label="OpenWeatherMap API Key (or leave blank to use OPENWEATHER_API_KEY env var)", type="password"),
            gr.Textbox(label="City name", placeholder="e.g., London"),
            gr.Dropdown(label="Units", choices=["metric", "imperial", "standard"], value="metric"),
        ],
        outputs=gr.Textbox(label="Result"),
        title="Simple Weather Demo",
        description="Enter your OpenWeatherMap API key and a city name to fetch current weather. This demo uses the Weather class from Weather.py.",
        allow_flagging="never",
        examples=[["", "London", "metric"],],
    )
    return iface


if __name__ == "__main__":
    app = build_interface()
    # Launch for a single user / prototype
    app.launch()