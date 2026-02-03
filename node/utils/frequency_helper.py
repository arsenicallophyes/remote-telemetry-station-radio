"""
Verify the frequency selected falls within the unlicensed regulations bands.
Limits and channels imposed on the LoRaWAN protocol do not apply to this project
thus the full spectrum of EU863-870 can be utilized.
"""
from typing import Iterable
from exceptions.regulations.licensed_frequency_error import LicensedFrequencyError
from regulations.band import Band

class FrequencyHelper:
    """
    Validate set frequency falls within the unlicensed range of the band.
    """

    @staticmethod
    def validate_frequency_in_bands(frequency_mhz: float, bands: Iterable[Band]) -> Band:
        """
        Return the matching Band if the frequency is legal; else raise LicensedFrequencyError
        """
        for b in bands:
            if b.start <= frequency_mhz <= b.end:
                return b

        raise LicensedFrequencyError(frequency_mhz)
