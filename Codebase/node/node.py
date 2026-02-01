"""
Define object node
"""
from uuid import UUID
from functools import wraps
from typing import Callable, Any

import board
import busio
import digitalio
import adafruit_rfm9x

from Codebase.models.packet import Packet
from Codebase.models.model import SpreadingFactor, CodingRate
from Codebase.models.packet_type import PacketType as pt


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
        self.rfm9x     = None
        self.__initialized_radio = False
        self.apply_link_profile(
            sf=7,
            bw=125000,
            cr=5,
            tx_power_dbm=23,
            crc=True,
            preamble=8
        )

    def init_radio__(self, freq: int) -> None:
        """
        Initialize radio pins for Challenger RP2040 868 MHz
        
        :param self: Description
        """
        if self.__initialized_radio:
            return
        cs           = digitalio. DigitalInOut(board.GP9)
        reset        = digitalio.DigitalInOut(board.GP13)
        spi          = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
        self.rfm9x   = adafruit_rfm9x.RFM9x(spi, cs, reset, freq)
        self.__initialized_radio = True

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
    def send(self, packet: Packet) -> None:        
        # self.rfm9x.send()
        print(packet)

    @require_radio_initialized
    def receive(self) -> Packet:
        node = Node(self.name, self.node_id)
        packet = Packet(node, node, pt.ACK, "TEMP")
        return packet
