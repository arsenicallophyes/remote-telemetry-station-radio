DutyCyclesType = float
class DutyCycles:
    DC_0_1   = 0.1
    DC_1     = 1.0
    DC_10    = 10.0
    DC_100   = 100.0

    @staticmethod
    def to_hourly_budget(value: float) -> float:
        return (value / 100.0) * 3600
