# script.py
import google.generativeai as genai
import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API key
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

FASTAPI_BASE_URL = "http://127.0.0.1:8000"

# --- Helper ---
def get_default_dates():
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    return tomorrow, day_after

# --- Tool definitions ---
trip_planner_tools = [
    {
        "function_declarations": [
            {
                "name": "find_flights",
                "description": "Searches for available flights between two locations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string"},
                        "destination": {"type": "string"},
                        "departure_date": {"type": "string"},
                        "return_date": {"type": "string"},
                        "adults": {"type": "integer"},
                    },
                    "required": ["origin", "destination", "departure_date"]
                }
            },
            {
                "name": "get_hotels",
                "description": "Searches for hotels in a location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "destination": {"type": "string"},
                        "max_results": {"type": "integer"},
                        "min_rating": {"type": "number"}
                    },
                    "required": ["destination"]
                }
            },
            {
                "name": "build_itinerary",
                "description": "Finds attractions, restaurants, and points of interest.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "days": {"type": "integer"}
                    },
                    "required": ["city", "days"]
                }
            }
        ]
    }
]

# --- Call FastAPI backend ---
def call_trip_planner_api(function_call):
    function_name = function_call.name
    args = dict(function_call.args) if function_call.args else {}

    try:
        if function_name == "find_flights":
            departure, _ = get_default_dates()
            request_body = {
                "origin": args["origin"],
                "destination": args["destination"],
                "departure_date": args.get("departure_date", departure),
                "adults": args.get("adults", 1)
            }
            if "return_date" in args:
                request_body["return_date"] = args["return_date"]
            res = requests.post(f"{FASTAPI_BASE_URL}/find_flights", json=request_body)
            res.raise_for_status()
            return json.dumps(res.json())

        elif function_name == "get_hotels":
            request_body = {
                "destination": args["destination"],
                "max_results": args.get("max_results", 5)
            }
            if "min_rating" in args:
                request_body["min_rating"] = args["min_rating"]
            res = requests.post(f"{FASTAPI_BASE_URL}/find_hotels", json=request_body)
            res.raise_for_status()
            return json.dumps(res.json())

        elif function_name == "build_itinerary":
            params = {k: v for k, v in args.items() if v is not None}
            res = requests.get(f"{FASTAPI_BASE_URL}/find_places", params=params)
            res.raise_for_status()
            return json.dumps(res.json())

        else:
            return json.dumps({"error": f"Unknown function {function_name}"})

    except Exception as e:
        return json.dumps({"error": str(e)})
