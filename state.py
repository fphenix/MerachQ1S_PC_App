from dataclasses import dataclass
from threading import Lock
from copy import deepcopy
from constants import DRAG

@dataclass(slots=True)
class FtmsData:
    connection: str = "Recherche..."
    elapsed_time: float=0
    distance: float=0
    power: float=0
    power_avg: float=0
    stroke_rate: float=0
    stroke_rate_avg: float=0
    stroke_count: int=0
    split_avg: float=0
    kcal: float=0

@dataclass(slots=True)
class SessionData:
    corrected_distance: float=0
    work_j: float=0

@dataclass(slots=True)
class Snapshot:
    ftms: FtmsData
    session: SessionData

class RowState:
    def __init__(self):
        self._lock=Lock()
        self.ftms=FtmsData()
        self.session=SessionData()
        self._last_time=None

    def reset_session(self):
        """
        Remet à zéro les statistiques de la séance.
        Les données FTMS reçues du rameur sont conservées.
        """

        with self._lock:

            self.session = SessionData()

            #
            # Le prochain time_elapsed reçu
            # ne doit pas créer un énorme dt.
            #
            self._last_time = self.ftms.elapsed_time
        
    def set_connection(self, status: str):
        """
        Met à jour l'état de la connexion Bluetooth.
        """
        
        with self._lock:

            self.ftms.connection = status

    def update_ftms(self,data:dict):
        with self._lock:
            dt=0
            if "time_elapsed" in data:
                t=float(data["time_elapsed"])
                dt=0 if self._last_time is None else max(0,t-self._last_time)
                self._last_time=t
                self.ftms.elapsed_time=t
            mapping={
                "distance_total":"distance",
                "power_instant":"power",
                "power_average":"power_avg",
                "stroke_rate_instant":"stroke_rate",
                "stroke_rate_average":"stroke_rate_avg",
                "stroke_count":"stroke_count",
                "split_time_average":"split_avg",
                "energy_total":"kcal",
            }
            for k,a in mapping.items():
                if k in data:
                    setattr(self.ftms,a,data[k])
            if dt>0:
                self.session.work_j+=self.ftms.power*dt
                if self.ftms.power>0:
                    v=(self.ftms.power/DRAG)**(1/3)
                    self.session.corrected_distance+=v*dt

    def snapshot(self):
        with self._lock:
            return Snapshot(deepcopy(self.ftms),deepcopy(self.session))
