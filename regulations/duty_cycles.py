from enum import Enum

class DutyCycles(Enum):
    DC_0_1   = 0.1
    DC_1     = 1.0
    DC_10    = 10.0
    DC_100   = 100.0

    def to_hourly_budget(self) -> float:
        return (self.value / 100.0) * 3600
