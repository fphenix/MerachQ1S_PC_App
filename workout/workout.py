class Workout:

    def __init__(self, filename: str | None = None):
        self.title: str = "Placeholder Workout"
        self.field: str = "Placeholder Field"
        self.steps: list = []
        self.filename: str = filename

    # -------------------------------------------------------------------------
    @property
    def total_seconds(self):
        return sum(
            step.duration_seconds
            for step in self.steps
        )

    # -------------------------------------------------------------------------
    def clear(self):
        self.title = "Placeholder Workout"
        self.field = "Placeholder Field"
        self.steps.clear()
        self.filename = None
