from workout.step import WorkoutStep

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
