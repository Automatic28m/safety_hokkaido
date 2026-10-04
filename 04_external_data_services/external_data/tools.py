from external_data.models import LiveDataSnapshot
from external_data.weather import fetch_real_time_weather
from external_data.disaster import fetch_disaster_warnings
from external_data.train import fetch_train_status
from external_data.trains import fetch_live_train_status
from external_data.flights import fetch_flight_status
from external_data.roads import fetch_road_status

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
        "description": "Check real-time operational status, delays, and disruptions for JR Hokkaido train lines.",
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

LIVE_TRAIN_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "check_live_train_status",
        "description": "Fetch live real-time operational status and delay reports for JR Hokkaido train lines from Yahoo Transit.",
        "parameters": {
            "type": "object",
            "properties": {
                "line_name": {
                    "type": "string",
                    "description": "The train line to inspect, e.g. 'Rapid Airport', 'Chitose Line', 'Hakodate Line', or 'All'"
                }
            }
        }
    }
}

FLIGHT_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "check_flight_status",
        "description": "Check flight operational status, cancellations, and delays for Hokkaido airports (default: CTS).",
        "parameters": {
            "type": "object",
            "properties": {
                "airport_code": {
                    "type": "string",
                    "description": "The 3-letter IATA airport code, default is 'CTS' (New Chitose Airport)."
                },
                "direction": {
                    "type": "string",
                    "enum": ["arrival", "departure", "both"],
                    "description": "Specify 'arrival' for incoming flights, 'departure' for outgoing flights, or 'both'. Default is 'arrival'. Use 'both' ONLY if absolutely necessary to save API quota."
                }
            }
        }
    }
}

ROAD_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "check_road_status",
        "description": "Check real-time road conditions, closures, and mountain pass winter hazards for Hokkaido expressways and highways.",
        "parameters": {
            "type": "object",
            "properties": {
                "region": {
                    "type": "string",
                    "description": "The region or road section in Hokkaido to inspect, default is 'Hokkaido'."
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
    """Checks live real-time operational status for JR Hokkaido train lines."""
    return fetch_train_status(line_name)


def check_live_train_status(line_name: str = "All") -> LiveDataSnapshot:
    """Fetches live JR Hokkaido operational transit status from Yahoo Transit or ODPT."""
    return fetch_live_train_status(line_name)


def check_flight_status(airport_code: str = "CTS", direction: str = "arrival") -> LiveDataSnapshot:
    """Fetches real-time flight status and delays from AviationStack."""
    return fetch_flight_status(airport_code, direction)


def check_road_status(region: str = "Hokkaido") -> LiveDataSnapshot:
    """Fetches real-time road conditions and closures from Hokkaido Road Information portal."""
    return fetch_road_status(region)


ROUTE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_route_estimate",
        "description": "Calculate estimated driving or travel time between two cities or landmarks using OSRM.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {
                    "type": "string",
                    "description": "Starting location, e.g., 'New Chitose Airport', 'Sapporo'"
                },
                "destination": {
                    "type": "string",
                    "description": "Destination, e.g., 'Otaru', 'Niseko'"
                },
                "mode": {
                    "type": "string",
                    "description": "Travel mode (vehicle, train, walk). Default is vehicle."
                }
            },
            "required": ["origin", "destination"]
        }
    }
}


def get_route_estimate(origin: str, destination: str, mode: str = "vehicle") -> LiveDataSnapshot:
    """Fetches estimated route distance and duration using OSRM API."""
    from external_data.routing import fetch_osrm_route_estimate
    return fetch_osrm_route_estimate(origin, destination, mode)
