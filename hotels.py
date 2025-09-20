import json
import os
import re
import subprocess
from typing import Optional
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv 
import requests

load_dotenv()
HOTEL_API_KEY = os.getenv("HOTEL_API_KEY")

router_hotel=APIRouter()

class HotelRequest(BaseModel):
    destination: str
    max_results: Optional[int] = 5
    min_rating: Optional[float] = 0
    
@router_hotel.post("/find_hotels")
async def get_hotels(request: HotelRequest):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "tripadvisor",
        "q": request.destination,
        "ssrc": "h",
        "api_key": HOTEL_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Tripadvisor may return hotels under 'locations' or 'local_results'
    locations = data.get("locations") or data.get("local_results") or []

    hotels_list = []
    for loc in locations:
        # rating may be missing, default to 0
        rating = float(loc.get("rating", 0) or 0)
        # Apply filters safely
        if rating < request.min_rating:
            continue
        
        hotel_name = loc.get("title", "N/A")
        hotel_location = loc.get("location", "N/A")
        hotel_description = loc.get("description", "N/A")
        
        hotels_list.append({
            "name": loc.get("title", "N/A"),
            "rating": rating,
            "reviews": loc.get("reviews", "N/A"),
            "other locations": loc.get("location", "N/A"),
            "description": loc.get("description", "N/A"),
            "link": loc.get("link", "N/A"),
            "top review": loc.get("highlighted_review","N/A"),
            "booking_info": "Visit link for booking options and best prices." # Added info
        })

        if len(hotels_list) >= request.max_results:
            break

    if not hotels_list:
        return {"destination": request.destination, "hotels": [], "message": "No hotels matched the filters. Try lowering min_rating or max_price."}

    return {"destination": request.destination, "hotels": hotels_list}