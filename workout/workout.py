class Workout:

    def __init__(self, filename: str | None = None):
        self.title = "Workout"
        self.field = "Field"
        self.steps = []
        self.filename = filename

    @property
    def total_seconds(self):
        return sum(
            step.duration_seconds
            for step in self.steps
        )

    def clear(self):
        self.title = "Workout"
        self.field = "Field"
        self.steps.clear()
