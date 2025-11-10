"""
Define custom error for utilizinig licensed frequencies.
"""
from Codebase.regulations.regulation_error import RegulationError

class LicensedFrequencyError(RegulationError):
    """
    Raised when a licensed frequncy is accessed without an appropiate
    license or authorization.
    """
    def __init__(self, frequency: float, region: str = "EU", ) -> None:
        message = (
            f"Unauthorized usage of {frequency:.3f} MHz detected in '{region}'. "
            "A valid license is required."
            ""
        )
        super().__init__(message, code=101)
        self.frequency = frequency
        self.region = region
