import os
import requests
import json
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
import pprint
from datetime import timedelta

load_dotenv()

# ----- Tool that calls your FastAPI API -----
def get_flights(origin: str, destination: str, depart_date: str):
    """
    Finds one-way flight information for a given origin, destination, and departure date.
    Args:
        origin (str): Starting city or airport.
        destination (str): Destination city or airport.
        depart_date (str): Departure date in YYYY-MM-DD format.
    """
    api_url = "http://127.0.0.1:8000/find_flights"
    payload = {
        "origin": origin,
        "destination": destination,
        "depart_date": depart_date
    }
    print(f"-> API call to {api_url} with: {json.dumps(payload)}")
    try:
        response = requests.post(api_url, json=payload)
        if response.status_code != 200:
            print("Error calling FastAPI:", response.text)
            return []
        return response.json()
    except requests.exceptions.RequestException as e:
        print("API connection failed:", str(e))
        return []
    
def get_hotels(destination: str, max_results: int = 5, min_rating: float = 0):
    """
    Finds hotel information for a given destination.

    Args:
        destination (str): The city or area to search for hotels.
        max_results (int, optional): Maximum hotels to return.
        min_rating (float, optional): Minimum rating to include.
    """
    api_url = "http://127.0.0.1:8000/find_hotels"
    payload = {
        "destination": destination,
        "max_results": max_results,
        "min_rating": min_rating
    }
    print(f"-> API call to {api_url} with: {json.dumps(payload)}")
    try:
        response = requests.post(api_url, json=payload)
        if response.status_code != 200:
            print("Error calling FastAPI:", response.text)
            return {}
        return response.json()
    except requests.exceptions.RequestException as e:
        print("API connection failed:", str(e))
        return []


# ---- CLI Logic ----
def run_flight_agent():
    # Set up Gemini API
    try:
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    except KeyError:
        print("\nError: GOOGLE_API_KEY env variable not set.")
        print("Run this in your terminal before starting: export GOOGLE_API_KEY='YOUR_API_KEY'")
        return

    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        tools=[get_flights, get_hotels]
    )
    chat = model.start_chat()

    today = datetime.now().strftime('%Y-%m-%d')
    system_instruction = f"Today's date is {today}. Always format dates as YYYY-MM-DD."
    print("describe your flight requirements: ")
    while True:
        prompt = input("\n> ")
        if prompt.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        # Ask Gemini for function call plan
        response = chat.send_message(content=prompt + "\n\n" + system_instruction)

        try:
            function_call = response.candidates[0].content.parts[0].function_call
            if function_call.name == "get_flights":
                print(f"\n-> Gemini wants to call: '{function_call.name}'")
                args = {key: value for key, value in function_call.args.items()}
                function_response = get_flights(**args)
                response = chat.send_message(
                    part=genai.types.Part(
                        function_response={
                            "name": "get_flights",
                            "response": {"result": function_response},
                        },
                    ),
                )
                flights_str = pprint.pformat(function_response)
                summary_prompt = (
                "Here is a list of flights:\n"
                f"{flights_str}\n\n"
                "From these, select and present ONLY the 5 best flights to the user, "
                "sorted by lowest price and then shortest duration. Show only these 5 and make it user-friendly."
                )
                response = chat.send_message(content=summary_prompt)
            
            elif function_call.name == "get_hotels":
                print(f"\n-> Gemini wants to call: '{function_call.name}'")
                args = {key: value for key, value in function_call.args.items()}
                function_response = get_hotels(**args)
                hotels_list = function_response.get("hotels", [])
                hotels_str = pprint.pformat(hotels_list)
                summary_prompt = (
                    f"Here is a list of hotels:\n{hotels_str}\n\n"
                "Select and present ONLY the 5 best hotels based on highest rating and present them user-friendly. "
                "If fewer than 5 are available, show all."
            )
                response = chat.send_message(content=summary_prompt)
        except (AttributeError, IndexError):
            pass

        print("\n--- Best Options ---")
        text_found = False
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text"):
                print(part.text)
                text_found = True
        if not text_found:
            print("No plain text reply from Gemini. Here is the raw response:")
            print(response.candidates[0].content.parts)
        print("--------------------------\n")

if __name__ == '__main__':
    run_flight_agent()
