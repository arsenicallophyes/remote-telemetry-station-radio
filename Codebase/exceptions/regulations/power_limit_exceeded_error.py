"""
Define custom error for exceeding permitted power usage.
"""
from Codebase.exceptions.regulations.regulation_error import RegulationError

class PowerLimitExceededError(RegulationError):
    """
    Raised when the transmit power level exceeds the legal EIRP limit
    for the given band or region.
    """
    def __init__(self, power_dbm: float, limit_dbm: float, region: str = "EU", ) -> None:
        message = (
            f"Transmit power level of {power_dbm:.1f} dBm exceeds the legal limit "
            f"of {limit_dbm} dBm for region '{region}'."
            ""
        )
        super().__init__(message, code=102)
        self.power_dbm = power_dbm
        self.limit_dbm = limit_dbm
        self.region = region
