"""
Define node startup behavior
"""
from Codebase.models.region import Region
from Codebase.models.band import Band
from Codebase.node.utils.band_helper import BandHelper

class Startup:
    """
    Define node startup behavior
    """
    def __init__(self, cmdf: float, region: Region, band: Band) -> None:
        Region.validate(region)
        Band.validate(band)
        BandHelper(region, band).validate(cmdf)

if __name__ == "__main__":
    Startup(433.175, Region.EU, Band.EU433)
