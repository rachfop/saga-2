"""
Module to run the workflow.
"""

import uuid

from flask import Flask, jsonify, request
from temporalio.client import Client

from activities import BookVacationInput
from saga_workflows import BookWorkflow
from shared import TASK_QUEUE_NAME

app = Flask(__name__)


async def get_temporal_client() -> Client:
    """
    Connects to the Temporal server and returns a client instance.

    Returns:
        Client: Temporal client instance.
    """
    return await Client.connect("localhost:7233")


def generate_unique_username(name):
    return f'{name.replace(" ", "-").lower()}-{str(uuid.uuid4().int)[:6]}'


@app.route("/book", methods=["POST"])
async def book_vacation():
    """
    Endpoint to book a vacation.

    Returns:
        Response: JSON response with booking details or error message.
    """
    user_id = generate_unique_username(request.json.get("name"))
    attempts = request.json.get("attempts")
    car = request.json.get("car")
    hotel = request.json.get("hotel")
    flight = request.json.get("flight")

    input_data = BookVacationInput(
        attempts=int(attempts),
        book_user_id=user_id,
        book_car_id=car,
        book_hotel_id=hotel,
        book_flight_id=flight,
    )

    client = await get_temporal_client()

    result = await client.execute_workflow(
        BookWorkflow.run,
        input_data,
        id=user_id,
        task_queue=TASK_QUEUE_NAME,
    )

    response = {"user_id": user_id, "result": result}
    if result == "Voyage cancelled":
        response["cancelled"] = True
    else:
        try:
            car_booking = (
                result.split("Booked car: ")[1].split("Booked hotel: ")[0].strip()
            )
            hotel_booking = (
                result.split("Booked hotel: ")[1].split("Booked flight: ")[0].strip()
            )
            flight_booking = result.split("Booked flight: ")[1].strip()

            response.update(
                {
                    "cancelled": False,
                    "car": car_booking,
                    "hotel": hotel_booking,
                    "flight": flight_booking,
                }
            )
        except IndexError:
            response[
                "error"
            ] = "Incomplete booking results. Please check the booking details."

    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3002, debug=True)
