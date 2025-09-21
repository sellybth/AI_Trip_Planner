# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json

# Routers
from flights import router_flights
from hotels import router_hotel
from itinerary import router_places

# AI logic imports (keep in a separate file, e.g., script.py)
from script import call_trip_planner_api, genai, trip_planner_tools

app = FastAPI(
    title="DestinAI - Trip Planner AI Agent",
    description="Backend for flights, hotels, and itinerary planning using Gemini AI",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev; set to your React URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router_flights, tags=["Flights"])
app.include_router(router_hotel, tags=["Hotels"])
app.include_router(router_places, tags=["Places"])

@app.get("/")
def root():
    return {"message": "DestinAI backend is running."}

# ---------------- Chat Endpoint ----------------
class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    try:
        print("Received message:", request.message)

        # Initialize AI model with tools
        system_instruction_text = (
            "You are a helpful and efficient AI trip planner assistant. "
            "Format outputs clearly. Use find_flights, get_hotels, or build_itinerary tools "
            "to fetch information via the FastAPI backend and summarize results for the user."
        )

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            tools=trip_planner_tools,
            system_instruction=system_instruction_text
        )

        # Start stateless chat session with optional history
        chat = model.start_chat(history=request.history or [])
        response = chat.send_message(request.message)

        # ---------------- Safe function call check ----------------
        function_call = None
        try:
            if (
                hasattr(response, "candidates") and response.candidates
                and hasattr(response.candidates[0].content, "parts")
                and response.candidates[0].content.parts
                and hasattr(response.candidates[0].content.parts[0], "function_call")
                and response.candidates[0].content.parts[0].function_call
            ):
                function_call = response.candidates[0].content.parts[0].function_call
        except Exception as e:
            print("Function call check failed:", e)

        # ---------------- If AI wants to call a tool ----------------
        if function_call:
            print("Function call detected:", function_call.name)
            tool_output = call_trip_planner_api(function_call)

            # Convert API JSON to readable string
            try:
                parsed = json.loads(tool_output)
                tool_output_text = json.dumps(parsed, indent=2)
            except Exception:
                tool_output_text = str(tool_output)

            # Send the tool output back to AI for final user-friendly response
            final_response = chat.send_message(tool_output_text)
            return {"response": final_response.text}

        # ---------------- No function call ----------------
        return {"response": response.text}

    except Exception as e:
        print("Error in /chat endpoint:", e)
        return {"response": f"Error occurred: {e}"}

# ---------------- Run Uvicorn ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
