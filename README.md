# SAGAS with Temporal

This [tutorial](./tutorial.md) covers the implementation of the Sagas pattern using Temporal.

## Running the Example

To run the example, open four terminal instances and follow the instructions below.

### Prerequisites

Create a virtual environment:

```command
python3 -m venv venv
```

Activate your virtual environment:

```command
source .venv/bin/activate
```

Install the dependencies:

```command
pip install -r requirements.txt
```

### Step 1: Start Temporal Server

In the first terminal, start the Temporal server in development mode:

```command
temporal server start-dev
```

### Step 2: Start the Worker

In the second terminal, run the worker script:

```command
python run_worker.py
```

### Step 3: Start the Workflow

In the third terminal, run the workflow script:

```command
python run_workflow.py
```

## Run a Successful Booking

In the fourth terminal, run the following `curl` command to initiate a successful booking process.

### Input

```command
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

### Expected Output

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

## Run a Failed Booking

To simulate a booking failure, run the following `curl` command in the fourth terminal.

### Input

```command
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

### Expected Output

```json
{
  "cancelled": true,
  "result": "Voyage cancelled",
  "user_id": "jane-smith-609592"
}
```

## Formatting Documentation and Code

### Format Documentation

To format the documentation, run the following command:

```command
dprint fmt -c dprint.json
```

### Format Python Examples

To format the Python examples in the documentation, run the following command:

```command
blacken-docs tutorial.md
```

### Format Code

To format the code, run the following commands:

```command
isort . && black .
```

If you need further assistance or have any questions, feel free to ask.
