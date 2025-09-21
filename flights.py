import os
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

booking_url_flight = "https://booking-com.p.rapidapi.com/v1/flights/search"
booking_url_location="https://booking-com.p.rapidapi.com/v1/flights/locations"
BOOKING_API_KEY = os.getenv("BOOKING_API_KEY")

router_flights = APIRouter()

class FlightRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str # Change to match the tool definition
    # You'll also need to add return_date if you want to support it in the FastAPI endpoint
    return_date: Optional[str] = None # Add this
    adults: Optional[int] = 1

def flight_location(city:str):
    headers = {
        "x-rapidapi-key": BOOKING_API_KEY,
	    "x-rapidapi-host": "booking-com.p.rapidapi.com"
    }
    params = {
        "name":city,
        "locale" : "en-gb"
    }

    city=requests.get(booking_url_location, headers=headers, params=params)
    city_data=city.json()
    for item in city_data:
        if item.get("type") == "AIRPORT" and item.get("code"):
            return item.get("code")
    return None


@router_flights.post("/find_flights")
def find_flights(req: FlightRequest):
    origin = flight_location(req.origin)
    destination = flight_location(req.destination)

    if not origin or not destination:
        raise HTTPException(status_code=400, detail="Could not find airport codes for the provided city names.")
    
    headers = {
        "x-rapidapi-key": BOOKING_API_KEY,
        "x-rapidapi-host": "booking-com.p.rapidapi.com"
    }
    params = {
        "from_code": origin,
        "to_code": destination,
        "depart_date": req.departure_date,
        "flight_type": "ROUNDTRIP" if req.return_date else "ONEWAY",
        "order_by": "BEST",
        "cabin_class": "ECONOMY",
        "currency": "INR",
        "locale": "en-gb",
        "stops": "0",
        "adults": req.adults or 1
    }
    resp = requests.get(booking_url_flight, headers=headers, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Flight API error")
    
    data = resp.json()
    flights = data.get('flightOffers', data)
    results = []

    for flight in flights:
        flight_info = {
            "segments": [],
            "flight_cost": flight.get('priceBreakdown', {}).get('total', {}).get('units')
        }
        for segment in flight.get('segments', []):
            segment_info = {
                "depart_time": segment.get('departureTime'),
                "arrive_time": segment.get('arrivalTime'),
                "legs": []
            }
            for leg in segment.get('legs', []):
                try:
                    airline = None
                    flight_num = None
                    carriers = leg.get("carriersData", [])
                    if carriers:
                        airline = carriers[0].get("name")
                    flight_num = leg.get('flightInfo', {}).get('flightNumber')

                    leg_info = {
                        "airline": airline,
                        "flight_num": flight_num
                    }
                    segment_info["legs"].append(leg_info)
                except Exception as e:
                    print("Error parsing leg:", e)
            flight_info["segments"].append(segment_info)
        results.append(flight_info)
    
    return {"flights": results}

