"""
Define custom error for unregistred bands.
"""
from typing import Tuple

from exceptions.regulations.regulation_error import RegulationError

class UnkownBandError(RegulationError):
    """
    Raised when the band provided is not registered.
    """
    def __init__(self, band_name: str, registered_bands: Tuple[str, ...]) -> None:
        message = (
            f"Band '{band_name}' is not registered within the following list: "
            f"{registered_bands}. Verify the band is registered."
        )
        super().__init__(message, code=104)
        self.band_name = band_name
        self.registered_bands = registered_bands
