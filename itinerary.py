# itinerary.py
from fastapi import FastAPI, Query, APIRouter
import requests
import math
import subprocess
import json
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()
PLACES_API_KEY = os.getenv("PLACES_API_KEY")
router_places=APIRouter()

def search_tripadvisor(city: str, ssrc: str = "A", limit: int = 30) -> List[Dict[str, Any]]:
    """
    Search TripAdvisor via SerpAPI.
    ssrc: 'A' = things to do, 'r' = restaurants
    """
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "tripadvisor",
        "q": city,
        "ssrc": ssrc,
        "limit": limit,
        "api_key": PLACES_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("TripAdvisor search error:", e)
        return []

    locations = data.get("locations", []) or []
    results = []

    for loc in locations:
        try:
            rating = float(loc.get("rating")) if loc.get("rating") not in (None, "") else None
        except (TypeError, ValueError):
            rating = None
        results.append({
            "title": loc.get("title"),
            "rating": rating,
            "reviews": int(loc.get("reviews")) if loc.get("reviews") else None,
            "address": loc.get("location"),
            "link": loc.get("link"),
            "position": loc.get("position"),
            "thumbnail": loc.get("thumbnail"),
            "description": loc.get("description"),
            "location_id": loc.get("location_id"),
            "location_type": loc.get("location_type"),
        })
    return results

@router_places.get("/find_places")
def build_itinerary(
    city: str,
    days: int,
    attractions_limit: int = 60,
    restaurants_limit: int = 30
) -> Dict[str, Any]:
    """
    Builds a JSON-friendly itinerary with attractions + meal suggestions.
    The number of days is fully dynamic based on user input.
    """
    if days < 1:
        days = 1

    attractions = search_tripadvisor(city, ssrc="A", limit=attractions_limit)
    restaurants = search_tripadvisor(city, ssrc="r", limit=restaurants_limit)

    if not attractions:
        return {"error": f"No attractions found for {city}"}

    # Sort by rating then reviews
    def score(item):
        return ((item.get("rating") or 0), (item.get("reviews") or 0))
    
    attractions.sort(key=score, reverse=True)
    restaurants.sort(key=score, reverse=True)

    per_day = max(1, math.ceil(len(attractions) / days))
    plan = {}

    for i in range(days):
        start = i * per_day
        end = start + per_day
        day_attractions = attractions[start:end]

        # Safe selection of restaurants using modulo
        lunch = restaurants[(i * 2) % len(restaurants)] if restaurants else None
        dinner = restaurants[(i * 2 + 1) % len(restaurants)] if restaurants else None

        plan[f"Day {i+1}"] = {
            "attractions": day_attractions,
            "lunch_suggestion": lunch,
            "dinner_suggestion": dinner
        }

    return {"city": city, "days": days, "plan": plan}