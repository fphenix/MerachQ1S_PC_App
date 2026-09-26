from workout.step import WorkoutStep

# Cannot use a simple "from setup.utils import clamp_to_zero"
# because of a circular dependency between this file and utils.py.
import setup.utils as utils

# =============================================================================
class Workout:

    def __init__(self, filename: str | None = None) -> None:

        self.title: str = "Placeholder Workout"
        self.field: str = "Placeholder Field"
        self.steps: list[WorkoutStep] = []
        self.filename: str | None = filename

    # -------------------------------------------------------------------------
    @property
    def total_seconds(self) -> float:

        return sum(
            step.duration_seconds
            for step in self.steps
        )

    # -------------------------------------------------------------------------
    def clear(self) -> None:
        
        self.title = "Placeholder Workout"
        self.field = "Placeholder Field"
        self.steps.clear()
        self.filename = None

    # -------------------------------------------------------------------------
    def find_step(
        self,
        elapsed_time: float,
    ) -> tuple[int, float] | None:

        if not self.steps:
            return None

        remaining = utils.clamp_to_zero(float(elapsed_time))
        last_index = len(self.steps) - 1

        for index, step in enumerate(self.steps):

            duration = utils.clamp_to_zero(
                float(step.duration_seconds)
            )

            if remaining < duration or index == last_index:
                return index, min(remaining, duration)

            remaining -= duration

        return None
