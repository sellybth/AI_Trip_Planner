from fastapi import FastAPI
from flights import router_flights
from hotels import router_hotel
from itinerary import router_places

app = FastAPI(
    title="Trip Planner AI Agent",
    description="Microservice for finding best flights using Tripadvisor API (RapidAPI). Orchestratable for hotel and attraction planning.",
)

app.include_router(router_flights, tags=["Flights"])
app.include_router(router_hotel, tags=["Hotels"])
app.include_router(router_places, tags=["Places"])

@app.get("/")
def root():
    return {"message": "Trip Planner AI backend is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
