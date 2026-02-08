"""
Define object node
"""
from uuid import UUID
from functools import wraps
from typing import Callable, Any, Optional, cast

import board
import busio
import digitalio
from adafruit_rfm9x import RFM9x

from node.mac.airtime import Airtime
from node.mac.duty_cycle_tracker import DutyCycleTracker

from models.packet import Packet
from models.model import SpreadingFactor, CodingRate
from models.packet_type import PacketType as pt
from regulations.types.model import BandTuple


# Adafruit RFM9X library does not support implicit
# header mode, thus spreading factor 6 is not supported.
# Spreading factor 6 requires an implicit header, as 
# specified by the RFM95W Lora modem datasheet.
IMPLICIT_HEADER_MODE = False

def require_radio_initialized(method: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(method)
    def wrapper(self: object, *args: Any, **kwargs: Any):
        if not getattr(self, "_Node__initialized_radio", False):
            raise RuntimeError(
                f"{method.__name__}() called before radio initialization"
            )
        return method(self, *args, **kwargs)
    return wrapper

class Node:
    """
    Node class
    """
    def __init__(self, name: str, node_id: UUID) -> None:
        """
        Initialize class Node.

        :param name: Node's name
        :param node_id: Node's unique identifier
        """
        self.name      = name
        self.node_id   = node_id

        self.dc_tracker   = DutyCycleTracker()

        self.__initialized_radio       = False
        self.rfm9x: Optional[RFM9x]    = None

    def init_radio__(self, freq: int, bands: BandTuple) -> None:
        """
        Initialize radio pins for Challenger RP2040 868 MHz
        
        :param self: Description
        """
        if self.__initialized_radio:
            return
        cs           = digitalio. DigitalInOut(board.GP9)
        reset        = digitalio.DigitalInOut(board.GP13)
        spi          = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
        self.rfm9x   = RFM9x(spi, cs, reset, freq)
        self.__initialized_radio = True

        for b in bands:
            self.dc_tracker.register_band(b.name, b.duty_cycle)

    @require_radio_initialized
    def apply_link_profile(
        self,
        sf: SpreadingFactor,
        bw: int,
        cr: CodingRate,
        tx_power_dbm: int,
        crc: bool = True,
        preamble: int = 8,
        ) -> None:
        r = self.rfm9x
        if r is None:
            return
        r.spreading_factor = sf
        r.signal_bandwidth = bw
        r.coding_rate = cr
        r.tx_power = tx_power_dbm
        r.enable_crc = crc
        r.preamble_length = preamble

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, value: object) -> bool:
        return value == self.name

    def __str__(self) -> str:
        return self.name

    @require_radio_initialized
    def transmit(self, packet: Packet) -> None:
        r = cast(RFM9x, self.rfm9x)
        # Additional 4 bytes added by the RFM9x library due to explicit header mode
        packet_bytes = len(packet.to_byte()) + 4
        packet_time = Airtime.total_time(
            r.signal_bandwidth,
            r.spreading_factor,
            r.preamble_length,
            packet_bytes,
            IMPLICIT_HEADER_MODE,
            r.low_datarate_optimize,
            r.coding_rate,
            r.crc_error()
        )
        # self.dc_tracker.validate_can_transmit("",packet_time)


    @require_radio_initialized
    def receive(self) -> Packet:
        node = Node(self.name, self.node_id)
        packet = Packet(node, node, pt.ACK, "TEMP")
        return packet
