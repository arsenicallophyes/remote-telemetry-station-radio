"""
Define Duty Cycle Tracker class
"""
from typing import Dict

from node.mac.types.band_airtime import BandAirtime

from regulations.duty_cycles import DutyCycles
from exceptions.regulations.unknown_band_error import UnkownBandError
from exceptions.regulations.duty_cycle_exceeded_error import DutyCycleExceededError

class DutyCycleTracker:
    """
    Duty Cycle class to keep track of air time used to transmit data frames per sub band, per hour.
    """
    def __init__(self) -> None:
        self.bands_airtime: Dict[str, BandAirtime] = {}

    def register_band(self, band_name: str, dc: DutyCycles):
        band_airtime = BandAirtime(band_name, dc)
        self.bands_airtime[band_name] = band_airtime

    def validate_can_transmit(self, band_name: str, packet_time: float):
        band_airtime = self.bands_airtime.get(band_name)

        if band_airtime is None:
            registered_bands = tuple(self.bands_airtime.keys())
            raise UnkownBandError(band_name, registered_bands)

        self.__validate_airtime(packet_time, band_airtime)

    def __validate_airtime(self, packet_time: float, band_airtime: BandAirtime) -> None:
        if not band_airtime.can_commit(packet_time):
            raise DutyCycleExceededError(
                band_airtime.dc,
                band_airtime.hourly_budget,
                band_airtime.name,
            )

    def commit_airtime(self, band_name: str, packet_time: float) -> None:
        self.bands_airtime[band_name].commit(packet_time)
