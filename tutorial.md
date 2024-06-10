---
title: Implement the Saga Pattern in Python Using Temporal
---

In today's interconnected digital landscape, ensuring consistency and reliability in multi-step processes is paramount.
When dealing with distributed systems, a failure in one service can lead to a domino effect, compromising the entire transaction.
The Saga pattern offers a solution to this problem by allowing distributed transactions to be broken into smaller, manageable transactions, each with its own compensation logic in case of failure.

The Saga pattern is a design pattern that provides a mechanism to manage long-running transactions and ensure data consistency across multiple services.
Instead of a single monolithic transaction, the Saga pattern breaks the transaction into smaller, manageable steps (Activities), each with its own compensation logic.
If any step fails, previously completed steps are undone using compensating transactions to maintain consistency.

In this guide, you will implement the Saga pattern using Temporal in Python to manage the booking process for cars, hotels, and flights.
This approach ensures that even if one part of the booking fails, the system can gracefully handle the rollback of previous steps, maintaining data consistency.

When you're finished, you'll be able to handle complex distributed transactions with ease and reliability using Temporal.

## Prerequisites

Before you begin, ensure you have the following:

- Familiarity with asynchronous programming in Python
- Basic understanding of microservices and distributed systems
- [Flask with async extras](https://flask.palletsprojects.com/en/2.3.x/async-await/):
  - `pip install flask[async]`

Now that you have the necessary prerequisites, you will start by creating the Activities for the booking process.
These Activities form the core tasks your Workflow will perform, interacting with external services and handling potential failures.

## Create Activities

In this step, you will create the booking Activities for cars, hotels, and flights.

These Activities will interact with external services, and you will simulate failures by raising exceptions if a service is unavailable.

First, create a new file named `activities.py`.
This file will contain the definitions of the Activities needed for the booking process.

Import the necessary modules:

```python
import asyncio
from temporalio import activity
from shared import BookVacationInput
```

The `asyncio` library is used for asynchronous operations.
The `activity` module from the `temporalio` library provides decorators and functions for defining Activities.
The `BookVacationInput` data class will be used to pass input data to the Activities.

Next, define the `book_car`, `book_hotel`, and `book_flight` Activities.
These Activities interact with external services.
After defining the booking Activities, you'll be ready to move on to handling the compensations, ensuring that any failed step can be rolled back gracefully

For this example, you will simulate a failure by raising exceptions if the number of attempts is less than the allowed number of attempts or if the booking ID is invalid.
The function will return a success message if no errors occur.

```python
@activity.defn
async def book_car(input: BookVacationInput) -> str:
    await asyncio.sleep(3)
    if activity.info().attempt < input.attempts:
        activity.heartbeat(
            f"Invoking activity, attempt number {activity.info().attempt}"
        )
        await asyncio.sleep(3)
        raise RuntimeError("Car service is down")

    if "invalid" in input.book_car_id:
        raise Exception("Invalid car booking, rolling back!")

    print(f"Booking car: {input.book_car_id}")
    return f"Booked car: {input.book_car_id}"
```

The `book_hotel` and `book_flight` functions follow a similar structure:

```python
@activity.defn
async def book_hotel(input: BookVacationInput) -> str:
    await asyncio.sleep(3)
    if activity.info().attempt < input.attempts:
        activity.heartbeat(
            f"Invoking activity, attempt number {activity.info().attempt}"
        )
        await asyncio.sleep(3)
        raise RuntimeError("Hotel service is down")

    if "invalid" in input.book_hotel_id:
        raise Exception("Invalid hotel booking, rolling back!")

    print(f"Booking hotel: {input.book_hotel_id}")
    return f"Booked hotel: {input.book_hotel_id}"


@activity.defn
async def book_flight(input: BookVacationInput) -> str:
    await asyncio.sleep(3)
    if activity.info().attempt < input.attempts:
        activity.heartbeat(
            f"Invoking activity, attempt number {activity.info().attempt}"
        )
        await asyncio.sleep(3)
        raise RuntimeError("Flight service is down")

    if "invalid" in input.book_flight_id:
        raise Exception("Invalid flight booking, rolling back!")

    print(f"Booking flight: {input.book_flight_id}")
    return f"Booked flight: {input.book_flight_id}"
```

With the main booking Activities in place, it's time to define the compensation Activities.
These undo actions are crucial for maintaining data consistency by rolling back successful steps if a subsequent step fails.

### Define Compensation Activities

For every action (`book_car`, `book_hotel`, and `book_flight`), you will create a corresponding undo action.
These Activities will log the undo action and return a success message.

```python
@activity.defn
async def undo_book_car(input: BookVacationInput) -> str:
    print(f"Undoing booking of car: {input.book_car_id}")
    return f"Undoing booking of car: {input.book_car_id}"


@activity.defn
async def undo_book_hotel(input: BookVacationInput) -> str:
    print(f"Undoing booking of hotel: {input.book_hotel_id}")
    return f"Undoing booking of hotel: {input.book_hotel_id}"


@activity.defn
async def undo_book_flight(input: BookVacationInput) -> str:
    print(f"Undoing booking of flight: {input.book_flight_id}")
    return f"Undoing booking of flight: {input.book_flight_id}"
```

By setting up these compensations, you'll ensure that your system can handle failures gracefully.
Next, you'll focus on defining shared data classes and constants to support your Activities and Workflows.

## Define Shared Data Classes and Constants

Shared data classes and constants are used to pass data between Activities and Workflows.
Common mistakes include using mutable data types such as lists or dictionaries, which can cause unexpected behavior.

Also, Task Queues are shared resources that can be used by multiple Workflows and Workers.

Create a new file named `shared.py`:

```python
from dataclasses import dataclass


@dataclass
class BookVacationInput:
    book_user_id: str
    book_car_id: str
    book_hotel_id: str
    book_flight_id: str
    attempts: int


TASK_QUEUE_NAME = "saga-task-queue"
```

These classes and constants will be used in both Activities, Workflows, and Workers.

Workflows order and run the execution of Activities.
With your Activities and shared data classes defined, the next step is to create the Workflow.
This Workflow coordinates the execution of Activities and handle compensations to maintain consistency in case of failures.

## Create the Workflow Definition

In the context of Temporal Workflows, compensation refers to the actions taken to roll back a transaction if an error occurs.
Each step in the Workflow has a corresponding compensation step that is executed in reverse order if the Workflow encounters an error.

This ensures that the system is returned to a consistent state, even in the case of partial failures.

Create a new file named `saga_workflows.py`.
This file will define your Workflow, which is responsible for executing your Activities in the correct order and handling compensation if necessary.

First, import the necessary modules:

```python
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities import BookVacationInput, book_car, book_flight, book_hotel
```

Next, create the `BookWorkflow` class and define the compensation actions, as well as the functions that execute your core logic: `book_car`, `book_hotel`, and `book_flight`.

These executions are wrapped in a `try` and `except` block to handle any exceptions and trigger compensations.

```python
@workflow.defn
class BookWorkflow:
    @workflow.run
    async def run(self, input: BookVacationInput):
        compensations = []

        try:
            # Attempt to book a car
            compensations.append("undo_book_car")
            output = await workflow.execute_activity(
                book_car,
                input,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(
                    non_retryable_error_types=["Exception"],
                ),
            )

            # Attempt to book a hotel
            compensations.append("undo_book_hotel")
            output += " " + await workflow.execute_activity(
                book_hotel,
                input,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(
                    non_retryable_error_types=["Exception"],
                ),
            )

            # Attempt to book a flight
            compensations.append("undo_book_flight")
            output += " " + await workflow.execute_activity(
                book_flight,
                input,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=1),
                    maximum_attempts=input.attempts,
                    non_retryable_error_types=["Exception"],
                ),
            )

            # If all bookings are successful, return the output
            return output
        except Exception:
            # If an error occurs, execute compensations in reverse order
            for compensation in reversed(compensations):
                await workflow.execute_activity(
                    compensation,
                    input,
                    start_to_close_timeout=timedelta(seconds=10),
                )

            # Return a message indicating the booking process was cancelled
            return "Voyage cancelled"
```

The `compensations` list keeps track of the actions that need to be undone in case of a failure.
Each compensation action is appended to this list after its corresponding booking action is successfully completed.
The `try` block attempts to execute each booking activity (`book_car`, `book_hotel`, `book_flight`) in sequence.
Each activity execution includes a retry policy to handle transient errors.
If any activity fails, the `except` block catches the exception and executes the compensation activities in reverse order to undo the previously completed steps.
This ensures the system is returned to a consistent state. The retry policy specifies how to handle retries for each activity, including non-retryable error types and retry intervals.

Having defined the Workflow, you're now ready to set up the Worker that will execute these Workflows and Activities.

## Define the Worker

The Worker is a crucial component that executes the defined Workflows and Activities.
Setting up the Worker correctly will ensure that your system can process tasks efficiently and reliably.

Create a new file named `run_worker.py`.

Import the necessary modules, including the `asyncio` library, Temporal `Client`, and `Worker`.
You will also import the Activities declared in the `activities.py` file.

```python
import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from activities import (
    book_car,
    book_flight,
    book_hotel,
    undo_book_car,
    undo_book_flight,
    undo_book_hotel,
)
from saga_workflows import BookWorkflow
from shared import TASK_QUEUE_NAME
```

With the Worker defined and ready to execute Workflows and Activities, the next step is to create the Client to initiate the booking process.

### Define the Worker

The Worker is a crucial component that executes the defined Workflows and Activities.
Setting up the Worker correctly will ensure that your system can process tasks efficiently and reliably.

In the `main()` function, you will specify how to connect to the Temporal server, create a Worker, and run it.
This Worker will listen to the specified Task Queue and execute the defined Workflows and Activities.

```python
interrupt_event = asyncio.Event()


async def main():
    # Connect to the Temporal server
    client = await Client.connect("localhost:7233")

    # Create a Worker that listens to the specified task queue
    worker = Worker(
        client,
        task_queue=TASK_QUEUE_NAME,
        workflows=[BookWorkflow],
        activities=[
            book_car,
            book_hotel,
            book_flight,
            undo_book_car,
            undo_book_hotel,
            undo_book_flight,
        ],
    )
    await worker.run()
    try:
        await interrupt_event.wait()
    finally:
        print("\nShutting down the worker\n")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nInterrupt received, shutting down...\n")
        interrupt_event.set()
        loop.run_until_complete(loop.shutdown_asyncgens())
```

The `Client.connect()` line connects to the Temporal server running on `localhost` at port `7233`.
This can be modified to run a Worker on Temporal Cloud.

The `Worker` is initialized with the client, the task queue name, the list of Workflows, and the list of Activities.
This setup ensures the Worker knows which tasks to listen for and execute.
The `await worker.run()` line starts the Worker, making it ready to receive tasks and execute the corresponding Activities and Workflows.

**Start the Worker**

To start the Worker, run the following command in your terminal:

```bash
python run_worker.py
```

Once the Worker is running, it will be ready to execute Workflows and Activities as tasks are submitted to the specified task queue.

Now that the Worker is set up and running, you can set up the Client to initiate the booking process.

## Create the Client

The Client is responsible for initiating the Workflow and handling the booking process.
Setting up the Client will allow you to interact with the Temporal server and trigger the booking Workflow.

Create a new file named `run_workflow.py`:

First, import the necessary modules, including `uuid`, Flask, and Temporal `Client`.

```python
import uuid

from flask import Flask, jsonify, request
from temporalio.client import Client

from activities import BookVacationInput
from saga_workflows import BookWorkflow
from shared import TASK_QUEUE_NAME
```

Initialize the Flask app and set up the dependency injection for the Temporal client.

```python
app = Flask(__name__)


async def get_temporal_client():
    return await Client.connect("localhost:7233")
```

Define a route to handle the booking process.
This route will accept a `POST` request, extract the necessary data from the request, initiate the Workflow, and return the result.

```python
@app.route("/book", methods=["POST"])
async def book_vacation():
    # Extract data from the request
    user_id = f'{request.json.get("name").replace(" ", "-").lower()}-{str(uuid.uuid4().int)[:6]}'
    attempts = request.json.get("attempts")
    car = request.json.get("car")
    hotel = request.json.get("hotel")
    flight = request.json.get("flight")

    # Create the input object for the Workflow
    input = BookVacationInput(
        attempts=int(attempts),
        book_user_id=user_id,
        book_car_id=car,
        book_hotel_id=hotel,
        book_flight_id=flight,
    )

    # Get the Temporal client
    client = await get_temporal_client()

    # Execute the Workflow
    result = await client.execute_workflow(
        BookWorkflow.run,
        input,
        id=user_id,
        task_queue=TASK_QUEUE_NAME,
    )

    # Prepare the response based on the result
    response = {"user_id": user_id, "result": result}
    if result == "Voyage cancelled":
        response["cancelled"] = True
    else:
        result_list = result.split("Booked ")
        response["cancelled"] = False
        response["car"] = result_list[1].split(" Booking ")[0].title()
        response["hotel"] = result_list[2].split(" Booking ")[0].title()
        response["flight"] = result_list[2].split(" Booking ")[1].title()

    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
```

The route extracts the username, number of attempts, car, hotel, and flight information from the request JSON.

A `BookVacationInput` object is created with the extracted data, which will be passed to the Workflow.

The Temporal client is obtained using the `get_temporal_client()` function.

The Workflow is executed using `client.execute_workflow()`, passing the input object and other required parameters.
Based on the result of the Workflow execution, a response is prepared and returned.
If the booking process is cancelled, the response indicates this. Otherwise, it provides details about the booked car, hotel, and flight.

**Start the Client**

Now to start the Client, run the following command in your terminal:

```bash
python3 run_workflow.py
```

Once the Client is set up, you can start the booking process and see the Saga pattern in action.

## Start the Booking Process

To run the booking process, you can use the following `curl` command to send a `POST` request to the `/book` endpoint.
This request will trigger the Workflow, and you will receive a response with the booking details or a cancellation message.

```bash
curl -X POST http://localhost:3002/book \
-H "Content-Type: application/json" \
-d '{
    "name": "John Doe",
    "attempts": 5,
    "car": "valid-car-id",
    "hotel": "valid-hotel-id",
    "flight": "valid-flight-id"
}'
```

### Output

The expected output should be a JSON response similar to the following:

```json
{
  "cancelled": false,
  "car": "Car: valid-car-id",
  "flight": "Flight: valid-flight-id",
  "hotel": "Hotel: valid-hotel-id",
  "result": "Booked car: valid-car-id Booked hotel: valid-hotel-id Booked flight: valid-flight-id",
  "user_id": "john-doe-184942"
}
```

You've just
But what happens if the booking process fails?

You've successfully initiated and completed your booking process using the Saga pattern with Temporal in Python.
Next, you'll learn how to simulate errors to test the robustness of your implementation.

### Simulate an Error

To ensure your implementation can handle failures gracefully, you will simulate a booking failure.
This step will demonstrate how the Saga pattern with Temporal manages to rollback in case of errors.

To simulate a booking failure, you can use the following `curl` command. T
his request includes an invalid hotel booking ID, which will cause the booking process to fail and trigger the rollback process.

```bash
curl -X POST http://localhost:3002/book \
-H "Content-Type: application/json" \
-d '{
    "name": "Jane Smith",
    "attempts": 3,
    "car": "valid-car-id",
    "hotel": "invalid-hotel-id",
    "flight": "valid-flight-id"
}'
```

The value `invalid` will trigger an exception, causing the booking to rollback.

### Output

The expected output should be a JSON response similar to the following:

```json
{
  "cancelled": true,
  "result": "Voyage cancelled",
  "user_id": "jane-smith-609592"
}
```

In this case, the booking process was cancelled due to the invalid hotel booking ID.
The Saga pattern ensures that any completed bookings are rolled back, maintaining a consistent state.

This demonstrates how the Saga pattern with Temporal handles both successful and failing scenarios in the booking process.
Let's summarize what you've accomplished and discuss potential next steps.

## Conclusion

In this guide, you have implemented the Saga pattern using Temporal in Python to handle distributed transactions for booking services.
By following this guide, you now have a robust system that can gracefully handle failures and ensure data consistency across multiple services.
This implementation can be extended to various other use cases where multi-step processes need reliable and scalable orchestration.
