# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Union, Dict, Any
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
    allow_origins=["*"],
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

class MessagePart(BaseModel):
    text: str

class HistoryMessage(BaseModel):
    role: str
    parts: List[MessagePart] # Ensure parts are always objects with 'text'

class ChatRequest(BaseModel):
    message: str
    history: List[HistoryMessage] = Field(default_factory=list)

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    try:
        print("Received message:", request.message)

        # Convert the incoming history to the format expected by genai.GenerativeModel
        # This history will contain all *previous* messages (user and model)
        formatted_history = []
        for msg in request.history:
            formatted_parts = []
            for part in msg.parts: # msg.parts is already List[MessagePart]
                formatted_parts.append({"text": part.text}) # Ensure it's a dict for genai

            formatted_history.append({
                "role": msg.role,
                "parts": formatted_parts
            })

        # Initialize AI model with tools
        system_instruction_text = (
            "You are a helpful and efficient AI trip planner assistant. "
            "Your goal is to assist users in planning their trips by finding flights, hotels, and building itineraries. "
            "When a user asks for travel information, you should use the available tools to find the requested details. "
            "If information is given in a previous prompt do not ask the user to repeat it."
            "do not give the user direct api json response. try to format it in a user friendly and human way for ease of understanding."
            "Extract the key information from the API response and present it clearly to the user."
          
            "Summarize the flight details, hotel options, or itinerary points concisely."
            "if the user asks for a combined response of a full or any combinations of the tools. call the apis and fetch details or use the ones called before"
            "Always try to gather enough information from the user (e.g., origin, destination, dates, location, days) "
            "before making a tool call. Be polite and informative."
        )

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            tools=trip_planner_tools,
            system_instruction=system_instruction_text
        )

        # Start chat session with the *previous* conversation history
        # The current user message will be passed separately to send_message
        chat = model.start_chat(history=formatted_history)

        # --- CRITICAL CHANGE HERE ---
        # Pass the current user's message to chat.send_message()
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
        import traceback
        traceback.print_exc()
        return {"response": f"Error occurred: {e}"}

# ---------------- Run Uvicorn ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)