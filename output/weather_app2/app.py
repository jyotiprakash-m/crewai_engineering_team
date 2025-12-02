Your final answer must be the great and the most complete as possible, it must be outcome described.

import gradio as gr
from Weather import Weather, APIError


def fetch_weather(api_key: str, city: str) -> str:
    """
    Create a Weather client with the provided API key and fetch weather for the city.
    Returns a user-friendly multi-line string or an error message.
    """
    api_key = (api_key or "").strip()
    city = (city or "").strip()

    if not api_key:
        return "Error: Please provide an OpenWeatherMap API key."

    if not city:
        return "Error: Please enter a city name."

    try:
        w = Weather(api_key=api_key)
    except ValueError as exc:
        return f"Error creating Weather client: {exc}"

    try:
        info = w.get_weather_by_city(city)
        # Format the output nicely
        lines = [
            f"City: {info.get('city', 'N/A')}",
            f"Temperature: {info.get('temperature', 'N/A')}",
            f"Humidity: {info.get('humidity', 'N/A')}",
            f"Conditions: {info.get('conditions', 'N/A')}",
            f"Wind speed: {info.get('wind_speed', 'N/A')}",
        ]
        return "\n".join(lines)
    except ValueError as exc:
        return f"Invalid input: {exc}"
    except ConnectionError as exc:
        return f"Network error: {exc}"
    except APIError as exc:
        return f"API error: {exc}"
    except Exception as exc:
        return f"Unexpected error: {exc}"


title = "Simple Weather Demo"
description = "Enter your OpenWeatherMap API key and a city name to get current weather (prototype/demo)."

iface = gr.Interface(
    fn=fetch_weather,
    inputs=[
        gr.Textbox(label="OpenWeatherMap API Key", placeholder="Enter your API key here", lines=1),
        gr.Textbox(label="City Name", placeholder="e.g. London", lines=1),
    ],
    outputs=gr.Textbox(label="Weather Info"),
    title=title,
    description=description,
    allow_flagging="never",
    theme="default",
)

if __name__ == "__main__":
    iface.launch()