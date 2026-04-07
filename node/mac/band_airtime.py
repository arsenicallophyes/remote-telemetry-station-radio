from collections import deque
from time import monotonic # Replace with local comptaible function/implementaion

from regulations.duty_cycles import DutyCycles, DutyCyclesType
from node.mac.types.models import UsedTime, WaitTime
try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Tuple, Deque, Optional


class BandAirtime:

    def __init__(
            self,
            name: str,
            dc: DutyCyclesType,
        ) -> None:
        self.name = name
        self.dc = dc
        self._hourly_budget = DutyCycles.to_hourly_budget(dc)
        self._used_time: float = 0.0
        self._tx_log: "Deque[Tuple[float, float]]" = deque((), 128)

    _window_sec: int = 3600

    @property
    def hourly_budget(self) -> float:
        return self._hourly_budget

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

    def used(self, now: "Optional[float]" = None) -> "UsedTime":
        now = monotonic() if now is None else now
        self._prune(now)
        return UsedTime(self._used_time)
    
    def used_at(self, wait: "WaitTime", now: "Optional[float]" = None) -> "UsedTime":
        now = monotonic() if now is None else now
        self._prune(now)
        cutoff = now + wait - self._window_sec
        used = self._used_time

        for t, a in self._tx_log:
            if t < cutoff:
                used -= a
            else:
                break

        return UsedTime(max(0, used))

    def can_commit(self, packet_time: float, now: "Optional[float]" = None) -> bool:
        used_time = self.used(now)
        return used_time + packet_time <= self.hourly_budget

    def commit(self, packet_time: float, now: "Optional[float]" = None):
        now = monotonic() if now is None else now
        self._prune(now)
        self._tx_log.append((now, packet_time))
        self._used_time += packet_time

    def wait_until_legal(
            self,
            packet_time: float,
            now: "Optional[float]" = None
        ) -> "Tuple[UsedTime, WaitTime]":
        now = monotonic() if now is None else now

        used     = self.used(now)
        target   = used + packet_time - self.hourly_budget
        expired = 0
        wait_until_legal = WaitTime(float("inf"))

        # If the budget available is > used + p_time then legal
        if target <= 0:
            return used, WaitTime(0.0)

        if packet_time > self.hourly_budget:
            return used, wait_until_legal

        for t, a in self._tx_log:
            expired += a
            if expired >= target:
                wait_until_legal = WaitTime(max(0, t + self._window_sec - now))
                break

        return used, wait_until_legal
