from abc import ABC, abstractmethod

import threading

# =============================================================================
class ReplaySource:

    # -------------------------------------------------------------------------
    def __init__(self, filename, speed=1.0):
        self.filename = filename
        self.speed = speed

        self._thread: threading.Thread | None = None
        self._running = False

    # -------------------------------------------------------------------------
    # Abstract
    @abstractmethod
    def start(self):
        ...

    # -------------------------------------------------------------------------
    # Abstract
    @abstractmethod
    def stop(self):
        ...

    # -------------------------------------------------------------------------
    # Abstract
    @abstractmethod
    def _run(self):
        raise NotImplementedError