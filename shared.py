"""
Module for shared data structures and constants.
"""

from dataclasses import dataclass


@dataclass
class BookVacationInput:
    """
    Data class for storing input data for booking vacation.
    """

    book_user_id: str
    book_car_id: str
    book_hotel_id: str
    book_flight_id: str
    attempts: int


TASK_QUEUE_NAME = "saga-task-queue"

