from engine.calc import (
    calc_full_split,
    calc_deltatime,
    calc_delta,
)

from workout.split_data import WorkoutSplit

# =============================================================================
class WorkoutSplitCalculator:

    def __init__(self, settings) -> None:

        self.settings = settings

        self.workout = None

        self.splits: list[WorkoutSplit] = []

        self.current_step: int | None = None

        self._step_start_elapsed = 0.0
        self._step_start_distance = 0.0

        self._previous_elapsed: float | None = None
        self._previous_distance: float | None = None

    # -------------------------------------------------------------------------
    def reset(self, workout=None) -> None:

        self.workout = workout

        self.splits.clear()

        self.current_step = None

        self._step_start_elapsed = 0.0
        self._step_start_distance = 0.0

        self._previous_elapsed = None
        self._previous_distance = None

    # -------------------------------------------------------------------------
    def start(self, distance: float) -> None:

        self.current_step = 0

        self._step_start_elapsed = 0.0
        self._step_start_distance = max(
            0.0,
            distance,
        )

        self._previous_elapsed = 0.0
        self._previous_distance = self._step_start_distance

        self._ensure_split(0)

    # -------------------------------------------------------------------------
    def update(
        self,
        workout_elapsed: float,
        distance: float,
    ) -> None:

        if self.workout is None:
            return

        if not self.workout.steps:
            return

        workout_elapsed = max(
            0.0,
            workout_elapsed,
        )

        distance = max(
            0.0,
            distance,
        )

        step_index, step_elapsed = (
            self._find_step(workout_elapsed)
        )

        # -------------------------------------------------------------
        # Première donnée
        # Sécurité : si le calculateur n'a pas été démarré explicitement.
        # -------------------------------------------------------------

        if self.current_step is None:

            self.start(
                distance=distance,
            )

        # -------------------------------------------------------------
        # Un ou plusieurs steps ont été franchis.
        # -------------------------------------------------------------

        while self.current_step < step_index:

            boundary_elapsed = (
                self._step_start_elapsed
                + self.workout.steps[
                    self.current_step
                ].duration_seconds
            )

            boundary_distance = (
                self._interpolate_distance(
                    boundary_elapsed,
                    distance,
                    workout_elapsed,
                )
            )

            self._update_split(
                self.current_step,
                calc_deltatime(boundary_elapsed, self._step_start_elapsed),
                calc_delta(boundary_distance, self._step_start_distance),
            )

            # Nouveau step
            self.current_step += 1

            self._ensure_split(
                self.current_step
            )

            self._step_start_elapsed = (
                boundary_elapsed
            )

            self._step_start_distance = (
                boundary_distance
            )

        # -------------------------------------------------------------
        # Step courant
        # -------------------------------------------------------------

        current = self.current_step

        current_step = self.workout.steps[current]

        elapsed = calc_deltatime(
            workout_elapsed, self._step_start_elapsed
        )

        elapsed = min(
            elapsed,
            current_step.duration_seconds,
        )

        current_distance = max(
            0.0,
            calc_delta(distance, self._step_start_distance),
        )

        self._update_split(
            current,
            elapsed,
            current_distance,
        )

        # -------------------------------------------------------------
        # Mémorise la dernière mesure pour l'interpolation.
        # -------------------------------------------------------------

        self._previous_elapsed = (
            workout_elapsed
        )

        self._previous_distance = (
            distance
        )

    # -------------------------------------------------------------------------
    def _ensure_split(
        self,
        index: int,
    ) -> None:

        while len(self.splits) <= index:

            self.splits.append(
                WorkoutSplit()
            )

    # -------------------------------------------------------------------------
    def _update_split(
        self,
        index: int,
        elapsed: float,
        distance: float,
    ) -> None:

        split = self.splits[index]

        split.elapsed = max(
            0.0,
            elapsed,
        )

        split.distance = max(
            0.0,
            distance,
        )

        if split.distance > 0.0:

            split.pace = calc_full_split(
                dist=split.distance,
                time=split.elapsed,
                split_length= self.settings.split_length,
            )

        else:

            split.pace = 0.0

    # -------------------------------------------------------------------------
    def _find_step(
        self,
        elapsed: float,
    ) -> tuple[int, float]:

        remaining = elapsed

        last_index = (
            len(self.workout.steps) - 1
        )

        for index, step in enumerate(
            self.workout.steps
        ):

            duration = step.duration_seconds

            if (
                remaining < duration
                or index == last_index
            ):
                return index, remaining

            remaining -= duration

        return (
            last_index,
            self.workout.steps[
                last_index
            ].duration_seconds,
        )

    # -------------------------------------------------------------------------
    def _interpolate_distance(
        self,
        target_elapsed: float,
        current_distance: float,
        current_elapsed: float,
    ) -> float:

        if (
            self._previous_elapsed is None
            or self._previous_distance is None
        ):
            return current_distance

        delta_elapsed = calc_deltatime(
            current_elapsed, self._previous_elapsed
        )

        if delta_elapsed <= 0.0:
            return current_distance

        ratio = calc_deltatime(
            target_elapsed, self._previous_elapsed
        ) / delta_elapsed

        ratio = min(
            1.0,
            max(0.0, ratio),
        )

        return (
            self._previous_distance
            + calc_delta(
                current_distance, self._previous_distance
            ) * ratio
        )
