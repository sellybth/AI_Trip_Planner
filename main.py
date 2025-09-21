from fastapi import FastAPI
from pydantic import BaseModel
from flights import router_flights
from hotels import router_hotel
from itinerary import router_places
from typing import List
from script import call_trip_planner_api, genai, trip_planner_tools  # Import your AI agent logic

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

# --- New chat endpoint ---
class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    # Initialize Gemini AI model with tools
    system_instruction_text = (
        "You are a helpful and efficient AI trip planner assistant. "
        "Format all outputs clearly and in human-readable form."
    )
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        tools=trip_planner_tools,
        system_instruction=system_instruction_text
    )
    
    chat = model.start_chat(history=request.history)

    response = chat.send_message(request.message)

    # Check if the AI wants to call a function
    if response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        tool_output = call_trip_planner_api(function_call)
        # Send tool output back to AI for a final human-readable response
        final_response = chat.send_message(tool_output)
        return {"response": final_response.text}

    # No function call, just return AI's direct response
    return {"response": response.text}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
