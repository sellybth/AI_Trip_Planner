import google.generativeai as genai
import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

# --- Configuration ---
FASTAPI_BASE_URL = "http://127.0.0.1:8000"
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY")) # Ensure this env var is set!

# --- Helper to get default dates ---
def get_default_dates():
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after_tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    return tomorrow, day_after_tomorrow

# --- Define the Tools (Function Declarations for AI Studio) ---
trip_planner_tools = [
    {
        "function_declarations": [
            {
                "name": "find_flights",
                "description": "Searches for available flights between two locations on specified dates. Requires origin, destination, and departure date.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "The departure airport or city code (e.g., 'NYC', 'LAX', 'London Heathrow')."
                        },
                        "destination": {
                            "type": "string",
                            "description": "The arrival airport or city code (e.g., 'MIA', 'SFO', 'Paris Charles de Gaulle')."
                        },
                        "departure_date": {
                            "type": "string",
                            "description": "The date of departure in YYYY-MM-DD format. Default to tomorrow if not specified."
                        },
                        "return_date": {
                            "type": "string",
                            "description": "The date of return in YYYY-MM-DD format (optional, for round trips,assume one-way trip if return not specified). Must be after departure_date."
                        },
                        "adults": {
                            "type": "integer",
                            "description": "Number of adult passengers (default is 1)."
                        }
                    },
                    "required": ["origin", "destination","departure_date"] # LLM might infer dates
                }
            },
            {
                "name": "get_hotels",
                "description": "Searches for hotels in a specific location Can filter by minimum rating.dont use any dates for this",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "destination": {
                            "type": "string",
                            "description": "The city or region for hotel search (e.g., 'London', 'Paris')."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of hotel: take 5."
                        },
                        "min_rating": {
                            "type": "number", # Use 'number' for floats/doubles
                            "description": "Optional: Minimum rating for hotels (e.g., 3.5, 4.0). Hotels below this rating will be excluded.minimun is 0.0 and maximum is 5.0",
                            
                        }
                    },
                    "required": ["destination"] # LLM might infer dates
                }
            },
            {
                "name": "build_itinerary",
                "description": "Finds attractions, restaurants, or other points of interest near a specified location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The city or region to search for places (e.g., 'Paris', 'Rome')."
                        },
                        "days": {
                            "type": "integer",
                            "description": " Specifiy number of days for the itinerary (default is 1).dont take float take int"
                        }
                    },
                    "required": ["city","days"]
                }
            }
        ]
    }
]

# --- Function to call your FastAPI Endpoints ---
def call_trip_planner_api(function_call):
    """
    Acts as the middleware to translate LLM's function calls
    into actual HTTP requests to your FastAPI backend.
    Handles POST for flights/hotels and GET for places.
    """
    function_name = function_call.name
    # Convert Gemini function_call args (MapComposite) → plain dict
    args = dict(function_call.args) if function_call.args else {}


    print(f"AI wants to call: {function_name} with args: {args}")

    try:
        if function_name == "find_flights":
            departure_date_str = args.get("departure_date")
            return_date_str = args.get("return_date")

            # Apply default dates if not provided by LLM
            if not departure_date_str:
                departure_date_str, _ = get_default_dates()
                print(f"Defaulting flight departure_date to: {departure_date_str}")
            
            # Note: The LLM might send "None" for optional parameters if it doesn't infer them.
            # We explicitly check for existence for return_date for defaulting.
            if return_date_str is None and "return_date" in args:
                 _, return_date_str = get_default_dates()
                 print(f"Defaulting flight return_date to: {return_date_str}")

            # Construct the request body for POST
            request_body = {
                "origin": args["origin"],
                "destination": args["destination"],
                "departure_date": departure_date_str, # Dates must be strings for JSON body
                "adults": args.get("adults", 1)
            }
            if return_date_str:
                request_body["return_date"] = return_date_str

            response = requests.post(f"{FASTAPI_BASE_URL}/find_flights", json=request_body)
            response.raise_for_status() # Raise an exception for HTTP errors
            return json.dumps(response.json())

        elif function_name == "get_hotels":


            # Construct the request body for POST
            request_body = {
                "destination": args["destination"],
                "max_results": args.get("max_results", 10),
            }
            # Only include min_rating if the LLM provided it, otherwise FastAPI will use its default (None)
            if args.get("min_rating") is not None:
                request_body["min_rating"] = args["min_rating"]

            response = requests.post(f"{FASTAPI_BASE_URL}/find_hotels", json=request_body)
            response.raise_for_status()
            return json.dumps(response.json())

        elif function_name == "build_itinerary":
            # This remains a GET request
            params = {
                "city": args["city"],
                "days": args.get("days")
            }
            # Filter out None values from params for cleaner URL
            params = {k: v for k, v in params.items() if v is not None}
            response = requests.get(f"{FASTAPI_BASE_URL}/find_places", params=params)
            response.raise_for_status()
            return json.dumps(response.json())

        else:
            return json.dumps({"error": f"Unknown function called: {function_name}"})

    except requests.exceptions.RequestException as e:
        print(f"Error calling FastAPI endpoint: {e}")
        return json.dumps({"error": f"API request failed: {e}"})
    except Exception as e:
        print(f"An unexpected error occurred in call_trip_planner_api: {e}")
        return json.dumps({"error": f"An unexpected error occurred: {e}"})


# --- Main AI Agent Loop ---
def run_trip_planner_agent():
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
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", tools=trip_planner_tools,system_instruction=system_instruction_text)
    chat = model.start_chat(history=[])

    print("Trip Planner AI Agent Ready. Type 'exit' to quit.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        try:
            response = chat.send_message(user_input)

            # Check if the model wants to call a function
            if response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                
                # Execute the function via your FastAPI bridge
                tool_output = call_trip_planner_api(function_call)
                # print(f"FastAPI returned: {tool_output}") # Uncomment for debugging

                # Send the tool output back to the model for a natural language response
                final_response = chat.send_message(tool_output)
                print(f"AI: {final_response.text}")

            else:
                # If no function call, just print the model's direct response
                print(f"AI: {response.text}")

        except Exception as e:
            print(f"An error occurred in the AI agent loop: {e}")
            # Optionally, you might want to log the full error or give a more specific message to the user

if __name__ == "__main__":
    run_trip_planner_agent()