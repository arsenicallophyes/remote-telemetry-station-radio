"""
Define custom error for exceeding air time of a band.
"""
from exceptions.regulations.regulation_error import RegulationError

class DutyCycleExceededError(RegulationError):
    """
    Raised when the duty cycle or air time exceeds legal threshold.
    """
    def __init__(self, duty_cycle: float, limit: float, band: str, region: str = "EU") -> None:
        message = (
            f"Duty cycle {duty_cycle:.2f}% exceeds the legal limit of {limit}% "
            f"for {band} band in region {region}. Reduce transmission rate or duration."
        )
        super().__init__(message, code=103)
        self.duty_cycle = duty_cycle
        self.limit = limit
        self.band = band
        self.region = region
