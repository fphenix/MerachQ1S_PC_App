from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from enum import Enum

import math

from setup.lang import get_text
from setup.utils import (
    is_between,
    clamp_to_zero, clamp_between,
    clamp_to_max, clamp_to_min,
)

from games.game import Game
from games.game_input import GameInput, input_cadence

# =============================================================================
@dataclass(slots=True)
class TowerBlock:

    x: float
    y: float
    angle: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    omega: float = 0.0
    landed: bool = False
    width: float = 70.0
    height: float = 36.0

# =============================================================================
class TowerGame(Game):

    GAME_ID: str = "tower"

    WIDTH: int = 1000
    HEIGHT: int = 700
    HUD_HEIGHT: int = 70
    DURATION_SECONDS: float = 600.0
    GROUND_Y: float = 620.0

    PLAYFIELD_WIDTH: float = 760.0
    BEAM_Y: float = 140.0
    BEAM_MIN_X: float = 90.0
    BEAM_MAX_X: float = 670.0
    BEAM_SPEED: float = 45.0
    CRANE_TOWER_CLEARANCE: float = 210.0  # Au moins 1/3 de la zone de jeu entre la tour et le bloc porté.
    CRANE_CARRIED_BLOCK_OFFSET: float = 45.0

    CHARGE_MIN_CPM: float = 16.0
    MOVE_TARGET: float = 22.0
    MOVE_MAX_CPM: float = 24.0
    HOLD_TARGET: float = 26.0
    HOLD_MAX_CPM: float = 28.0
    DROP_TARGET: float = 30.0
    MAX_CPM: float = 40.0

    CHARGE_RATE: float = 0.42
    DECAY_RATE: float = 0.08
    DROP_CHARGE_MIN: float = 0.72
    GRAVITY: float = 880.0
    RESTITUTION: float = 0.08
    FRICTION: float = 0.62
    SOLVER_ITERATIONS: int = 5

    STONE_SIZES: list[tuple[float, float]] = [(64.0, 32.0), (72.0, 38.0), (80.0, 34.0), (68.0, 42.0), (76.0, 36.0)]

    class BuildPhase(Enum):
        HOLD: str = "HOLD"
        MOVE: str = "MOVE"
        DROP: str = "DROP"

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__(game_id=self.GAME_ID, title=get_text("MENU_GAMES_TOWER"), duration=self.DURATION_SECONDS)
        
        self.reset()

    # -------------------------------------------------------------------------
    def reset(self) -> None:
        
        self.current_spm: float | None = None
        self.stack_x: float = self.PLAYFIELD_WIDTH * 0.5
        self.beam_x: float = self.stack_x
        self.beam_y: float = self.BEAM_Y
        self.pickup_side: int = 1
        self.carrying_block: bool = False
        self.beam_direction: float = 1.0
        self.blocks: list[TowerBlock] = []
        self.block_count: int = 0
        self.max_height_px: float = 0.0
        self.camera_offset_y: float = 0.0
        self._stroke_event_latched: bool = False
        self.drop_charge: float = 0.0
        self.cadence_state: TowerGame.BuildPhase = self.BuildPhase.HOLD
        self.score: int = 0
        self.bonus_score: int = 0

    # -------------------------------------------------------------------------
    def _next_block_size(self) -> tuple[float, float]:
        sizes = self.STONE_SIZES
        return sizes[self.block_count % len(sizes)]

    # -------------------------------------------------------------------------
    def _release_block(self) -> bool:

        if not self.carrying_block:
            return False
        if self.drop_charge < self.DROP_CHARGE_MIN:
            return False

        width, height = self._next_block_size()
        self.blocks.append(TowerBlock(
            x=self.beam_x, y=self.beam_y + self.CRANE_CARRIED_BLOCK_OFFSET,
            vy=15.0,
            width=width, height=height,
        ))
        self.block_count += 1
        self.carrying_block = False
        self.drop_charge = 0.0
        self.pickup_side *= -1

        return True

    # -------------------------------------------------------------------------
    def _move_crane(self, dt: float) -> None:

        step = self.BEAM_SPEED * clamp_between(dt, 0.0, 0.06)
        self.beam_x += self.beam_direction * step

        if self.beam_x >= self.BEAM_MAX_X:
            self.beam_x = self.BEAM_MAX_X
            self.beam_direction = -1.0
            if not self.carrying_block and self.pickup_side > 0:
                self.carrying_block = True

        elif self.beam_x <= self.BEAM_MIN_X:
            self.beam_x = self.BEAM_MIN_X
            self.beam_direction = 1.0
            if not self.carrying_block and self.pickup_side < 0:
                self.carrying_block = True

    # -------------------------------------------------------------------------
    def _update_crane_height(self) -> None:

        if self.max_height_px <= 0.0:
            return

        tower_top_y = self.GROUND_Y - self.max_height_px
        _, carried_height = self._next_block_size()

        carried_bottom_offset = self.CRANE_CARRIED_BLOCK_OFFSET + carried_height / 2.0
        target_beam_y = tower_top_y - self.CRANE_TOWER_CLEARANCE - carried_bottom_offset

        # La grue peut monter, mais ne redescend pas lorsque la tour s'effondre.
        self.beam_y = min(self.beam_y, target_beam_y)

    # -------------------------------------------------------------------------
    @staticmethod
    def _vertices(b: TowerBlock) -> list[tuple[float, float]]:
        c, s = math.cos(b.angle), math.sin(b.angle)
        hw, hh = b.width / 2, b.height / 2
        return [(b.x + x*c - y*s, b.y + x*s + y*c) 
                for x, y in ((-hw,-hh),(hw,-hh),(hw,hh),(-hw,hh))]

    # -------------------------------------------------------------------------
    @staticmethod
    def _axes(b: TowerBlock) -> tuple[tuple[float,float], tuple[float,float]]:
        c, s = math.cos(b.angle), math.sin(b.angle)
        return ((c,s),(-s,c))

    # -------------------------------------------------------------------------
    @staticmethod
    def _cross(a: tuple[float,float], b: tuple[float,float]) -> float:
        return (a[0] * b[1]) - (a[1] * b[0])

    # -------------------------------------------------------------------------
    @staticmethod
    def _inertia(b: TowerBlock) -> float:
        return clamp_to_min((b.width*b.width + b.height*b.height)/12.0, 1.0)

    # -------------------------------------------------------------------------
    @staticmethod
    def _point_velocity(b: TowerBlock | None, p: tuple[float,float]) -> tuple[float,float]:

        if b is None:
            return (0.0, 0.0)

        rx, ry = p[0]-b.x, p[1]-b.y
        return b.vx - b.omega*ry, b.vy + b.omega*rx

    # -------------------------------------------------------------------------
    def _impulse(self, a: TowerBlock, b: TowerBlock | None, normal: tuple[float,float], point: tuple[float,float]) -> None:
        
        va = self._point_velocity(a, point)
        vb = self._point_velocity(b, point)
        rv = (vb[0]-va[0], vb[1]-va[1])
        vn = rv[0]*normal[0] + rv[1]*normal[1]
        if vn >= 0:
            return

        ra = (point[0]-a.x, point[1]-a.y)
        rb = (point[0]-b.x, point[1]-b.y) if b else (0.0, 0.0)
        ia = 1/self._inertia(a)
        ib = 1/self._inertia(b) if b else 0.0
        ca = self._cross(ra,normal)
        cb = self._cross(rb,normal)
        denom = (1.0 + (1.0 if b else 0.0)) + ca*ca*ia + cb*cb*ib
        j = -(1+self.RESTITUTION)*vn / denom
        imp = (normal[0]*j, normal[1]*j)
        a.vx -= imp[0]
        a.vy -= imp[1]
        a.omega -= self._cross(ra,imp)*ia
        if b:
            b.vx += imp[0]
            b.vy += imp[1]
            b.omega += self._cross(rb,imp)*ib

        va = self._point_velocity(a,point)
        vb = self._point_velocity(b,point)
        rv = (vb[0]-va[0], vb[1]-va[1])
        t0 = rv[0]-(rv[0]*normal[0] + rv[1]*normal[1])*normal[0]
        t1 = rv[1]-(rv[0]*normal[0] + rv[1]*normal[1])*normal[1]
        tangent_raw = (t0, t1)
        tl = math.hypot(*tangent_raw) # longueur du vecteur  partir de son x=t0 et son y=t1, le "*" est un "unpack".
        if tl < 1e-7:
            return

        t = (tangent_raw[0]/tl, tangent_raw[1]/tl)
        cta, ctb = self._cross(ra,t), self._cross(rb,t)
        denom_t = (1.0 + (1.0 if b else 0.0)) + cta*cta*ia + ctb*ctb*ib
        jt = -(rv[0]*t[0]+rv[1]*t[1]) / denom_t
        jt = clamp_between(jt, -self.FRICTION*j, self.FRICTION*j)
        fi = (t[0]*jt, t[1]*jt)
        a.vx -= fi[0]
        a.vy -= fi[1]
        a.omega -= self._cross(ra,fi) * ia
        if b:
            b.vx += fi[0]
            b.vy += fi[1]
            b.omega += self._cross(rb,fi) * ib

    # -------------------------------------------------------------------------
    def _collide(self, a: TowerBlock, b: TowerBlock) -> bool:
        
        va, vb = self._vertices(a), self._vertices(b)
        if (
            max(p[0] for p in va) < min(p[0] for p in vb)
            or max(p[0] for p in vb) < min(p[0] for p in va)
        ):
            return False
        if (
            max(p[1] for p in va) < min(p[1] for p in vb)
            or max(p[1] for p in vb) < min(p[1] for p in va)
        ):
            return False

        overlap_min = float("inf")
        axis_min = (0.0, 1.0)
        for axis in self._axes(a)+self._axes(b):
            pa = [p[0] * axis[0] + p[1] * axis[1] for p in va]
            pb = [p[0] * axis[0] + p[1] * axis[1] for p in vb]
            overlap = min(max(pa),max(pb)) - max(min(pa),min(pb))
            if overlap <= 0:
                return False
            
            if overlap < overlap_min:
                overlap_min, axis_min = overlap, axis

        if (b.x-a.x) * axis_min[0] + (b.y-a.y) * axis_min[1] < 0:
            axis_min = (-axis_min[0], -axis_min[1])

        correction = clamp_to_zero(overlap_min - 0.05) * 0.42
        a.x -= axis_min[0] * correction / 2
        a.y -= axis_min[1] * correction / 2
        b.x += axis_min[0] * correction / 2
        b.y += axis_min[1] * correction / 2

        proj_a = [p[0] * axis_min[0] + p[1] * axis_min[1] for p in va]
        proj_b = [p[0] * axis_min[0] + p[1] * axis_min[1] for p in vb]
        edge_a = [p for p,v in zip(va,proj_a) if max(proj_a)-v < 1e-5]
        edge_b = [p for p,v in zip(vb,proj_b) if v-min(proj_b) < 1e-5]

        sa = (sum(p[0] for p in edge_a)/len(edge_a), sum(p[1] for p in edge_a)/len(edge_a))
        sb = (sum(p[0] for p in edge_b)/len(edge_b), sum(p[1] for p in edge_b)/len(edge_b))
        point=((sa[0]+sb[0])/2, (sa[1]+sb[1])/2)
        self._impulse(a, b, axis_min,point)
        a.landed = b.landed = True

        # Contact stone/stone très inélastique : amortit les vibrations lentes
        # qui, sans moteur physique externe, feraient osciller la pile indéfiniment.
        if abs(a.vy) < 80.0 and abs(b.vy) < 80.0:
            a.vy *= 0.55
            b.vy *= 0.55
        return True

    # -------------------------------------------------------------------------
    def _solve_physics(self, dt: float) -> None:
        
        step = clamp_to_max(dt, 0.06) / 2
        for _ in range(2):
            for b in self.blocks:
                b.vy += self.GRAVITY*step
                b.x += b.vx*step
                b.y += b.vy*step
                b.angle += b.omega*step
                b.vx *= 0.999
                b.vy *= 0.999
                b.omega *= 0.998
                vertices=self._vertices(b)
                contacts=[p for p in vertices if p[1]>self.GROUND_Y and 0<=p[0]<=self.PLAYFIELD_WIDTH]
                if contacts:
                    deepest_y=max(p[1] for p in contacts)
                    deepest=[p for p in contacts if deepest_y-p[1] < 1e-5]
                    p = (sum(q[0] for q in deepest)/len(deepest),sum(q[1] for q in deepest)/len(deepest))
                    b.y -= p[1]-self.GROUND_Y
                    self._impulse(b, None, (0.0, 1.0), p)
                    # Dissipation au contact du sol : évite qu'un bloc presque
                    # au repos rebondisse indéfiniment à cause du pas discret.
                    if abs(b.vy) < 80.0:
                        b.vy *= 0.32
                        b.vx *= 0.92
                        b.omega *= 0.72
                    b.landed=True

            for _ in range(self.SOLVER_ITERATIONS):
                for i,a in enumerate(self.blocks):
                    for b in self.blocks[i+1:]:
                        self._collide(a,b)
                # Les collisions entre blocs peuvent pousser la base dans le sol ;
                # on réapplique la contrainte à chaque itération pour propager
                # l'arrêt du sol vers les blocs empilés au-dessus.
                for b in self.blocks:
                    verts=self._vertices(b)
                    contacts=[p for p in verts if p[1]>self.GROUND_Y and 0<=p[0]<=self.PLAYFIELD_WIDTH]
                    if contacts:
                        deepest_y = max(p[1] for p in contacts)
                        b.y -= deepest_y-self.GROUND_Y
                        if b.vy > 0.0:
                            b.vy=0.0
                        b.vx *= 0.985
                        b.omega *= 0.96

        landed = [b for b in self.blocks if b.landed]
        if landed:
            top = min(min(p[1] for p in self._vertices(b)) for b in landed)
            self.max_height_px = clamp_to_min(self.max_height_px, self.GROUND_Y-top)
        self.score=int(clamp_to_zero(self.max_height_px + self.bonus_score))

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:
        
        self.current_spm = input_cadence(game_input)
        cadence = self.current_spm
        new_stroke = bool(game_input.stroke_event and not self._stroke_event_latched)
        self._stroke_event_latched = bool(game_input.stroke_event)

        is_move = cadence is not None and is_between(cadence, self.CHARGE_MIN_CPM, self.MOVE_MAX_CPM)
        is_hold = cadence is not None and is_between(cadence, self.MOVE_MAX_CPM, self.HOLD_MAX_CPM)
        is_drop = cadence is not None and is_between(cadence, self.HOLD_MAX_CPM, self.MAX_CPM)
        is_rowing = cadence is not None and is_between(cadence, self.CHARGE_MIN_CPM, self.MAX_CPM)

        # Trois zones de commande : MOVE, HOLD et DROP.
        if is_move:
            self.cadence_state = self.BuildPhase.MOVE
        elif is_hold:
            self.cadence_state = self.BuildPhase.HOLD
        elif is_drop:
            self.cadence_state = self.BuildPhase.DROP
        else:
            self.cadence_state = self.BuildPhase.HOLD

        # MOVE: La grue ne se déplace que dans la zone MOVE. HOLD permet d'ajuster
        # la cadence sans dérive, et DROP immobilise la grue pendant le dépôt.
        if self.cadence_state == self.BuildPhase.MOVE:
            self._move_crane(dt)

        # CHARGE: La charge se construit entre 16 et 40 CPM, indépendamment de la zone
        # de commande. Elle se vide progressivement uniquement sous 16 CPM (et quand un bloc est lâché).
        if is_rowing:
            self.drop_charge = clamp_to_max(
                self.drop_charge + clamp_to_zero(dt) * self.CHARGE_RATE, 1.0
            )
        else:
            self.drop_charge = clamp_to_zero(
                self.drop_charge - clamp_to_zero(dt) * self.DECAY_RATE
            )

        # DROP: Entrer dans DROP ne suffit pas : un nouveau coup est requis.
        if self.cadence_state == self.BuildPhase.DROP and self.carrying_block and new_stroke:
            self._release_block()

        self._solve_physics(dt)
        self._update_crane_height()

        top_y = self.GROUND_Y - self.max_height_px
        self.camera_offset_y = clamp_to_max(top_y - 355.0, 0.0)

    # -------------------------------------------------------------------------
    def on_finished(self) -> None:
        self.score=int(clamp_to_zero(self.max_height_px + self.bonus_score))


# =============================================================================
class Tower1Game(TowerGame):
    """Gameplay A : moteur Tower historique conservé sans mécanique B."""

    GAME_ID: str = "tower"


# =============================================================================
class Tower2Game(TowerGame):
    """Gameplay B : prise lente, sélection de colonne et chute après stabilité."""

    GAME_ID: str = "tower2"

    PICKUP_MIN_CPM: float = 10.0
    PICKUP_TARGET: float = 18.0
    PICKUP_MAX_CPM: float = 19.0
    COLUMN_TARGETS: tuple[int, ...] = (20, 24, 28, 32)
    COLUMN_TOLERANCE: float = 2.0
    STABILITY_SECONDS: float = 40.0
    COLUMN_BONUSES: tuple[int, ...] = (0, 20, 40, 50)
    COLUMN_X: tuple[float, ...] = (150.0, 325.0, 500.0, 660.0)

    # Nombre de coups récents visé : interpolation de 11 à 16 échantillons
    # entre 20 et 32 CPM, soit environ 80 % des coups attendus en 40 secondes.
    @classmethod
    def _sample_count_for_target(cls, target: float) -> int:
        return int(round(11.0 + (target - 20.0) * (5.0 / 12.0)))

    # -------------------------------------------------------------------------
    def __init__(self) -> None:
        super().__init__()
        self.title = get_text("MENU_GAMES_TOWER_B")

    # -------------------------------------------------------------------------
    def reset(self) -> None:
        super().reset()
        self.column_index: int | None = None
        self.stability_elapsed: float = 0.0
        self.stability_samples: deque[float] = deque(maxlen=16)
        self.bonus_score = 0
        self._last_stability_zone: int | None = None
        self.cadence_state = self.BuildPhase.HOLD

    # -------------------------------------------------------------------------
    @classmethod
    def _column_for_cadence(cls, cadence: float | None) -> int | None:
        if cadence is None:
            return None
        candidates = [
            (abs(cadence - target), index)
            for index, target in enumerate(cls.COLUMN_TARGETS)
            if abs(cadence - target) <= cls.COLUMN_TOLERANCE
        ]
        return min(candidates)[1] if candidates else None

    # -------------------------------------------------------------------------
    def _reset_stability(self, zone: int | None) -> None:
        self.stability_elapsed = 0.0
        self.stability_samples.clear()
        self._last_stability_zone = zone

    # -------------------------------------------------------------------------
    def _release_block(self) -> bool:
        if not self.carrying_block:
            return False
        # Le moteur commun crée le bloc et consomme sa charge. La charge est
        # rendue suffisante ici : B utilise la durée de stabilité, pas la jauge A.
        self.drop_charge = 1.0
        released = super()._release_block()
        if released and self.column_index is not None:
            self.bonus_score += self.COLUMN_BONUSES[self.column_index]
            self.score = int(clamp_to_zero(self.max_height_px + self.bonus_score))
        return released

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:
        cadence = input_cadence(game_input)
        self.current_spm = cadence
        new_stroke = bool(game_input.stroke_event and not self._stroke_event_latched)
        self._stroke_event_latched = bool(game_input.stroke_event)

        # La grue ne bouge vers la prise que dans la plage 10–19 CPM. Elle
        # poursuit ensuite sa cible de colonne sans dépendre du rafraîchissement
        # écran pour compter des coups ou alimenter la moyenne.
        is_pickup_cadence = cadence is not None and is_between(
            cadence, self.PICKUP_MIN_CPM, self.PICKUP_MAX_CPM
        )
        if not self.carrying_block and is_pickup_cadence:
            self._move_crane(dt)

        selected = self._column_for_cadence(cadence) if self.carrying_block else None
        if selected != self.column_index:
            self.column_index = selected
            self._reset_stability(selected)

        if self.carrying_block and selected is not None:
            target_x = self.COLUMN_X[selected]
            move_alpha = 1.0 - math.exp(-4.0 * clamp_between(dt, 0.0, 0.1))
            self.beam_x += (target_x - self.beam_x) * move_alpha
            self.cadence_state = self.BuildPhase.DROP
            if self._last_stability_zone != selected:
                self._reset_stability(selected)
            self.stability_elapsed += clamp_to_zero(dt)
            if new_stroke and cadence is not None:
                sample_count = self._sample_count_for_target(self.COLUMN_TARGETS[selected])
                if self.stability_samples.maxlen != sample_count:
                    self.stability_samples = deque(
                        self.stability_samples, maxlen=sample_count
                    )
                self.stability_samples.append(float(cadence))

            # La moyenne ne reçoit qu'un échantillon par véritable impulsion.
            # Dès qu'elle sort de la plage de la colonne, on invalide toute la
            # stabilité : les ticks d'affichage ne fabriquent jamais de données.
            if self.stability_samples:
                cadence_average = sum(self.stability_samples) / len(self.stability_samples)
                if abs(cadence_average - self.COLUMN_TARGETS[selected]) > self.COLUMN_TOLERANCE:
                    self._reset_stability(None)

            if self.stability_elapsed >= self.STABILITY_SECONDS:
                self._release_block()
                self.column_index = None
                self._reset_stability(None)
        else:
            self.cadence_state = self.BuildPhase.MOVE if is_pickup_cadence else self.BuildPhase.HOLD
            if self.carrying_block:
                # Sortie de la zone : aucun reliquat de durée ni d'échantillons.
                self._reset_stability(None)

        self._solve_physics(dt)
        self._update_crane_height()
        top_y = self.GROUND_Y - self.max_height_px
        self.camera_offset_y = clamp_to_max(top_y - 355.0, 0.0)

    # -------------------------------------------------------------------------
    def on_finished(self) -> None:
        self.score = int(clamp_to_zero(self.max_height_px + self.bonus_score))
