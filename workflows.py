from datetime import timedelta
from typing import List, Union

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

with workflow.unsafe.imports_passed_through():
    from activities import (
        BookVacationInput,
        book_car,
        book_flight,
        book_hotel,
        undo_book_car,
        undo_book_flight,
        undo_book_hotel,
    )


@workflow.defn
class BookingWorkflow:
    """
    Workflow class for booking a vacation.
    """

    @workflow.run
    async def run(self, book_input: BookVacationInput) -> Union[str, dict]:
        """
        Executes the booking workflow.

        Args:
            book_input (BookVacationInput): Input data for the workflow.

        Returns:
            str: Workflow result.
        """
        compensations: List[object] = []
        try:
            compensations.append(undo_book_car)
            output = await workflow.execute_activity(
                book_car,
                book_input,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(non_retryable_error_types=["ValueError"]),
            )
            compensations.append(undo_book_hotel)
            output += await workflow.execute_activity(
                book_hotel,
                book_input,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(non_retryable_error_types=["ValueError"]),
            )

            compensations.append(undo_book_flight)
            output += await workflow.execute_activity(
                book_flight,
                book_input,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=1),
                    maximum_attempts=book_input.attempts,
                    non_retryable_error_types=["ValueError"],
                ),
            )
            return {"status": "success", "message": output}
        except ActivityError as e:
            for compensation in reversed(compensations):
                await workflow.execute_activity(
                    compensation,
                    book_input,
                    start_to_close_timeout=timedelta(seconds=10),
                )
            return {"status": "failure", "error": str(e)}
