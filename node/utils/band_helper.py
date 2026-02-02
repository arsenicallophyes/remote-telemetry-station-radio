"""
Helper utility to automate frequency validation for all supported bands
"""
from types.region import Region
from types.band import Band
from node.utils.frequency_helper import FrequencyHelper

class BandHelper:
    """
    Helper utility to automate frequency validation for all supported bands
    """
    def __init__(self, region: Region, band: Band) -> None:
        self.region = region
        self.band   = band

    def validate(self, frequency: float) -> None:
        """
        Verify the frequency provided abides with unlicensed band and region laws.
        """
        if self.region == Region.EU:
            if self.band == Band.EU433:
                FrequencyHelper.Europe.validate_eu433(frequency)
                return
            if self.band == Band.EU863:
                FrequencyHelper.Europe.validate_eu863_870(frequency)
                return
        raise ValueError(f"Region {self.region} is disabled. Only EU is supported at the moment.")
