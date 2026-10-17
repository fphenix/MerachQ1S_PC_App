"""Variante Fishing 2 : contrôle par zones de cadence (Gameplay B)."""

from setup.lang import get_text

from games.fishing.engine import FishingGame

# =============================================================================
class Fishing2Game(FishingGame):
    """Même jeu que FishingGame, avec une règle de déplacement différente."""

    CADENCE_UP: float   = 28.0
    CADENCE_STAY: float = 24.0
    CADENCE_DOWN: float = 20.0
    CADENCE_MARGIN: float = 2.0

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__()
        
        self.game_id = "fishing2"
        self.title = get_text("MENU_GAMES_FISHING2")

    # -------------------------------------------------------------------------
    def _update_lane_from_spm(self, spm: float) -> None:

        # Gameplay B: >28 CPM monte d'un couloir, <20 descend d'un.
        # Les bornes 20 et 28 sont inclusives : elles maintiennent le couloir.
        if (
            spm > (self.CADENCE_UP - self.CADENCE_MARGIN)
            and self.lane_index < self.LANE_COUNT - 1
        ):
            self.lane_index += 1
        
        elif (
            spm < (self.CADENCE_DOWN + self.CADENCE_MARGIN)
            and self.lane_index > 0
        ):
            self.lane_index -= 1
        
        self._target_net_y = self._net_y_for_lane(self.lane_index)

    # -------------------------------------------------------------------------
    def _anticipate_lane_from_spm(self, spm: float) -> None:

        # L'anticipation descend une seule fois à chaque franchissement de
        # niveau (20, puis 16 CPM), sans répéter le mouvement à chaque frame.
        if self.lane_index > 0:
        
            down_threshold = self.CADENCE_LEVELS[self.lane_index] - 4.0
        
            if spm < down_threshold:
                self.lane_index -= 1
                self._target_net_y = self._net_y_for_lane(self.lane_index)
