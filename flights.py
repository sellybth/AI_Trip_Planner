import os
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

load_dotenv()

booking_url_flight = "https://booking-com.p.rapidapi.com/v1/flights/search"
booking_url_location="https://booking-com.p.rapidapi.com/v1/flights/locations"
BOOKING_API_KEY = os.getenv("BOOKING_API_KEY")

router_flights = APIRouter()

class FlightRequest(BaseModel):
    origin: str
    destination: str
    depart_date: str

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
        "depart_date": req.depart_date,
        "flight_type": "ONEWAY",
        "order_by": "BEST",
        "cabin_class": "ECONOMY",
        "currency": "INR",
        "locale": "en-gb",
        "stops": 0,
        "adults": 1
    }
    resp = requests.get(booking_url_flight, headers=headers, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Flight API error")
    data = resp.json()
    flights = data.get('flightOffers', data)  # adapt if your root is not 'flights'
    results = []
    for flight in flights:
        for segment in flight.get('segments', []):
            depart_time = segment.get('departureTime')
            arrive_time = segment.get('arrivalTime')
            for leg in segment.get('legs', []):
                for carrier in leg.get("carriersData", []):
                    airline=carrier.get("name")
            flight_num = leg.get('flightInfo', {}).get('flightNumber')
        cost = flight.get('priceBreakdown', {}).get('total', {}).get('units')
        results.append({
                'depart_time': depart_time,
                'arrive_time': arrive_time,
                'airline': airline,
                'flightnum':flight_num,
                'flight_cost':cost
        })
    # Print or further process the 'results' list
    return results

