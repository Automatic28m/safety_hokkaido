from external_data.models import LiveDataSnapshot
from external_data.weather import fetch_real_time_weather
from external_data.disaster import fetch_disaster_warnings
from external_data.train import fetch_train_status

# Tool schemas for LLM tool-calling interfaces
WEATHER_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_weather_for_city",
        "description": "Fetch structured real-time weather and hourly forecast snapshot for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The name of the city, e.g. Sapporo, Niseko, Hakodate, Asahikawa"
                }
            },
            "required": ["city"]
        }
    }
}

DISASTER_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_disaster_warnings",
        "description": "Fetch real-time disaster warnings (earthquakes, weather/snow warnings) from the Japan Meteorological Agency (JMA) for Hokkaido.",
        "parameters": {
            "type": "object",
            "properties": {
                "region": {
                    "type": "string",
                    "description": "The region to inspect, default is 'Hokkaido'."
                }
            }
        }
    }
}

TRAIN_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "check_train_status",
        "description": "Check simulated operational status and delays for JR Hokkaido train lines.",
        "parameters": {
            "type": "object",
            "properties": {
                "line_name": {
                    "type": "string",
                    "description": "The specific train line to inspect, e.g. 'Rapid Airport', 'Hakodate Line', or 'All'"
                }
            }
        }
    }
}


def get_real_time_weather(city_name: str) -> LiveDataSnapshot:
    """Fetches real-time weather returning a normalized LiveDataSnapshot."""
    return fetch_real_time_weather(city_name)


def get_disaster_warnings(region: str = "Hokkaido") -> LiveDataSnapshot:
    """Fetches real-time JMA disaster and warning feeds returning a normalized LiveDataSnapshot."""
    return fetch_disaster_warnings(region)


def check_train_status(line_name: str = "All") -> LiveDataSnapshot:
    """Checks JR Hokkaido status simulation returning a LiveDataSnapshot marked with status 'mocked'."""
    return fetch_train_status(line_name)
