"""
Define custom error for exceeding air time of a band.
"""
from exceptions.regulations.regulation_error import RegulationError
from regulations.duty_cycles import DutyCyclesType
class DutyCycleExceededError(RegulationError):
    """
    Raised when the duty cycle or air time exceeds legal threshold.
    """
    def __init__(self, duty_cycle: DutyCyclesType, limit: float, band: str) -> None:
        message = (
            f"Duty cycle {duty_cycle:.2f}% exceeds the legal limit of {limit}s per rolling hour. "
            f"for {band} band. Reduce transmission rate or duration."
        )
        super().__init__(message, code=103)
        self.duty_cycle = duty_cycle
        self.limit = limit
        self.band = band
