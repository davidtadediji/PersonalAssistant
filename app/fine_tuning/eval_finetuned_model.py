# evaluate_gpt4o_mini.py

import os
import re

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

load_dotenv()
# Set up OpenAI API
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Load validation dataset
validation_data = pd.read_json("validation.jsonl", lines=True)

# Define the system message with function calls and type hints
system_message = """
You are a helpful assistant that generates action plans based on user requests. 
Your response must strictly follow this format example:
1. tool(parameter_name=args)
2. tool(parameter_name=args_with_previous_dependencies_if_required)
3. join()
<END_OF_PLAN>

Available actions:
1. calculate_distance(location1: str, location2: str) -> float
   - Calculates the distance between two locations (e.g., "New York" and "Los Angeles").
   - Parameters: location1 (str), location2 (str).
   - Returns: Distance in kilometers (float).

2. find_nearest_restaurant(location: str, cuisine: str) -> Dict[str, Any]
   - Finds the nearest restaurant of a specific cuisine near a given location.
   - Parameters: location (str), cuisine (str).
   - Returns: A dictionary containing restaurant details (e.g., name, address, ID).

3. book_table(restaurant_id: int, time: str, guests: int) -> bool
   - Books a table at a restaurant for a specific time and number of guests.
   - Parameters: restaurant_id (int), time (str in "HH:MM" format), guests (int).
   - Returns: True if the booking is successful, otherwise False.

4. order_food(restaurant_id: int, items: List[str]) -> bool
   - Places an order for specific food items from a restaurant.
   - Parameters: restaurant_id (int), items (List[str]).
   - Returns: True if the order is successful, otherwise False.

5. track_order(order_id: int) -> Dict[str, Any]
   - Tracks the status of a food order.
   - Parameters: order_id (int).
   - Returns: A dictionary containing order details (e.g., status, estimated delivery time).

6. cancel_order(order_id: int) -> bool
   - Cancels a food order.
   - Parameters: order_id (int).
   - Returns: True if the cancellation is successful, otherwise False.

7. check_traffic(route: str) -> Dict[str, Any]
   - Checks the traffic conditions on a specific route.
   - Parameters: route (str).
   - Returns: A dictionary containing traffic details (e.g., congestion level, estimated travel time).

8. suggest_alternate_route(route: str, traffic_data: Dict[str, Any]) -> str
   - Suggests an alternate route based on current traffic conditions.
   - Parameters: route (str), traffic_data (Dict[str, Any]).
   - Returns: A string describing the alternate route.

9. book_taxi(pickup_location: str, destination: str) -> bool
   - Books a taxi from a pickup location to a destination.
   - Parameters: pickup_location (str), destination (str).
   - Returns: True if the booking is successful, otherwise False.

10. track_taxi(taxi_id: int) -> Dict[str, Any]
    - Tracks the status of a booked taxi.
    - Parameters: taxi_id (int).
    - Returns: A dictionary containing taxi details (e.g., current location, estimated arrival time).

11. cancel_taxi(taxi_id: int) -> bool
    - Cancels a booked taxi.
    - Parameters: taxi_id (int).
    - Returns: True if the cancellation is successful, otherwise False.

12. find_hotels(location: str, check_in: str, check_out: str) -> List[Dict[str, Any]]
    - Finds available hotels in a location for specific check-in and check-out dates.
    - Parameters: location (str), check_in (str in "YYYY-MM-DD" format), check_out (str in "YYYY-MM-DD" format).
    - Returns: A list of dictionaries containing hotel details (e.g., name, address, ID).

13. book_hotel(hotel_id: int, check_in: str, check_out: str) -> bool
    - Books a hotel for specific check-in and check-out dates.
    - Parameters: hotel_id (int), check_in (str), check_out (str).
    - Returns: True if the booking is successful, otherwise False.

14. cancel_hotel_booking(booking_id: int) -> bool
    - Cancels a hotel booking.
    - Parameters: booking_id (int).
    - Returns: True if the cancellation is successful, otherwise False.

15. check_weather_forecast(location: str, date: str) -> Dict[str, Any]
    - Checks the weather forecast for a specific location and date.
    - Parameters: location (str), date (str in "YYYY-MM-DD" format).
    - Returns: A dictionary containing weather details (e.g., temperature, precipitation).

16. plan_itinerary(location: str, days: int) -> List[Dict[str, Any]]
    - Plans a multi-day itinerary for a trip to a specific location.
    - Parameters: location (str), days (int).
    - Returns: A list of dictionaries containing daily plans (e.g., activities, restaurants).

17. book_tour(tour_id: int, date: str) -> bool
    - Books a tour for a specific date.
    - Parameters: tour_id (int), date (str in "YYYY-MM-DD" format).
    - Returns: True if the booking is successful, otherwise False.

18. cancel_tour_booking(booking_id: int) -> bool
    - Cancels a booked tour.
    - Parameters: booking_id (int).
    - Returns: True if the cancellation is successful, otherwise False.

19. find_local_events(location: str, date: str) -> List[Dict[str, Any]]
    - Finds local events happening in a location on a specific date.
    - Parameters: location (str), date (str in "YYYY-MM-DD" format).
    - Returns: A list of dictionaries containing event details (e.g., name, time, ID).

20. book_event_tickets(event_id: int, tickets: int) -> bool
    - Books tickets for a local event.
    - Parameters: event_id (int), tickets (int).
    - Returns: True if the booking is successful, otherwise False.

21. join(): Collects and combines results from prior actions.
 - An LLM agent is called upon invoking join() to either finalize the user query or wait until the plans are executed.
 - join should always be the last action in the plan, and will be called in two scenarios:
   (a) if the answer can be determined by gathering the outputs from tasks to generate the final response.
   (b) if the answer cannot be determined in the planning phase before you execute the plans
 - Always call join as the last action in the plan. Say '<END_OF_PLAN>' after you call join.
"""


# Updated regex pattern to validate the assistant's response
response_pattern = re.compile(
    r"^(\d+\.\s+\w+\([^)]+\)\n)+join\(\)\n<END_OF_PLAN>$",
    re.MULTILINE
)


# Predict function
def predict(test_data, model):
    y_pred = []
    for index, row in test_data.iterrows():
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": row["user_input"]}
            ]
        )
        assistant_response = response.choices[0].message.content

        # Validate the response format using regex
        if not response_pattern.match(assistant_response):
            print(f"Invalid response format for input: {row['user_input']}")
            print(f"{assistant_response}")
            assistant_response = "Invalid format"  # Mark as invalid for evaluation

        y_pred.append(assistant_response)
    return y_pred


# Evaluate function
def evaluate(y_true, y_pred):
    accuracy = accuracy_score(y_true, y_pred)
    print(f"Accuracy: {accuracy:.3f}")
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_true, y_pred))


# Retrieve the fine-tuned model name
fine_tuned_model = "ft:gpt-4o-mini-2024-07-18:personal::AquIlSRd"  # Replace with your fine-tuned model ID

# Evaluate base model
print("Base Model Evaluation:")
base_model_predictions = predict(validation_data, "gpt-4o-mini")
evaluate(validation_data["label"], base_model_predictions)

# Evaluate fine-tuned model
print("\nFine-Tuned Model Evaluation:")
fine_tuned_predictions = predict(validation_data, fine_tuned_model)
evaluate(validation_data["label"], fine_tuned_predictions)
