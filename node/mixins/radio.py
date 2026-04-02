from time import struct_time

import rtc # pyright: ignore[reportMissingModuleSource] # pylint: disable=import-error
import board
import busio
import digitalio
from adafruit_rfm9x_patched import RFM9x

from node.mac.duty_cycle_tracker import DutyCycleTracker
from node.mac.channel_selection import ChannelSelect
from regulations.types.model import BandsSeq


try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False  # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from models.model import SpreadingFactor, CodingRate



class RadioMixin:
    node_id : int
    dc_tracker: DutyCycleTracker
    channels: ChannelSelect

    def __init_rtc__(self):
        self.rtc = rtc.RTC()
        # Year, Month, Day, Hour, Minute, Second
        # Day of week, day of year, daylight saving flag: Last 3 fields ignored
        self.rtc.datetime = struct_time((2026, 3, 1, 12, 40, 10, 0, 0, -1))

    def __init_radio__(self, freq: float, bands: BandsSeq) -> None:
        """
        Initialize radio pins for Challenger RP2040 868 MHz
        
        :param self: Description
        """
        cs      = digitalio. DigitalInOut(board.GP9)
        reset   = digitalio.DigitalInOut(board.GP13)
        spi     = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
        rfm9x   = RFM9x(spi, cs, reset, freq)

        setattr(rfm9x, "node", self.node_id)

        self.rfm9x = rfm9x

        for b in bands:
            self.dc_tracker.register_band(b.name, b.duty_cycle)


    def apply_link_profile(
        self,
        sf: "SpreadingFactor",
        bw: int,
        cr: "CodingRate",
        tx_power_dbm: int,
        crc: bool = True,
        preamble: int = 8,
        ) -> None:

        r = self.rfm9x
        r.spreading_factor = sf
        r.signal_bandwidth = bw
        r.coding_rate = cr
        r.tx_power = tx_power_dbm
        r.enable_crc = crc
        r.preamble_length = preamble
