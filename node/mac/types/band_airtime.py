from dataclasses import dataclass, field
from collections import deque
from typing import Tuple, Deque, Optional
from time import monotonic # Replace with local comptaible function/implementaion

from regulations.duty_cycles import DutyCycles

@dataclass(slots=True)
class BandAirtime:
    name: str
    hourly_limit: float
    dc: DutyCycles

    _used_time: float = 0.0
    _tx_log: Deque[Tuple[float, float]] = field(default_factory=deque[Tuple[float, float]])
    _window_sec: int = 3600

    def _prune(self, now: float):
        cutoff = now - self._window_sec

        while self._tx_log and self._tx_log[0][0] < cutoff:
            self._remove_entry()

    def _remove_entry(self):
        _, a = self._tx_log.popleft()
        self._used_time -= a

        if self._used_time < 0:
            # Add log
            self._used_time = 0.0

    def _used(self, now: Optional[float] = None):
        now = monotonic() if now is None else now
        self._prune(now)
        return self._used_time

    def can_commit(self, packet_time: float, now: Optional[float] = None) -> bool:
        used_time = self._used(now)
        return used_time + packet_time <= self.hourly_limit

    def commit(self, packet_time: float, now: Optional[float] = None):
        now = monotonic() if now is None else now
        self._tx_log.append((now, packet_time))
        self._used_time += packet_time