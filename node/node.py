"""
Define object node
"""
from time import monotonic, sleep

import board
import busio
import digitalio
from adafruit_rfm9x_patched import RFM9x

from node.mac.airtime import Airtime
from node.mac.band_airtime import WaitTime
from node.mac.duty_cycle_tracker import DutyCycleTracker
from node.mac.band_selection import BandSelect
from node.mac.channel_selection import ChannelSelect

from models.packet import Packet
from models.model import SpreadingFactor, CodingRate
from models.packet_type import PacketType

from regulations.types.model import BandsSeq

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional, Tuple




# Adafruit RFM9X library does not support implicit
# header mode, thus spreading factor 6 is not supported.
# Spreading factor 6 requires an implicit header, as
# specified by the RFM95W Lora modem datasheet.
IMPLICIT_HEADER_MODE = False
APP_ACK_REQ   = 0x01  # request ACK
APP_ROUTED    = 0x02  # forwarded packet
APP_CONTROL   = 0x04  # control / management

class Node:
    """
    Node class
    """
    time_scale: float = 4.0
    formula_weights: "Tuple[float, float]" = 0.3, 0.4
    temp: float = 0.5
    min_control_reserve_ratio: float = 0.20
    allow_wait_candidates: bool = True
    wait_horizon_sec: WaitTime = WaitTime(15)

    def __init__(self, name: str, node_id: int, freq: int, bands: BandsSeq) -> None:
        """
        Initialize class Node.

        :param name: Node's name
        :param node_id: Node's unique identifier
        """
        self.name      = name
        self.node_id   = node_id

        self.dc_tracker   = DutyCycleTracker()
        self.channels     = ChannelSelect(125.0)

        self.init_radio__(freq, bands)


    def init_radio__(self, freq: int, bands: BandsSeq) -> None:
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
        sf: SpreadingFactor,
        bw: int,
        cr: CodingRate,
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

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, value: object) -> bool:
        return value == self.name

    def __str__(self) -> str:
        return self.name

    def transmit(self, packet: Packet, now: "Optional[float]" = None) -> None:
        now = monotonic() if now is None else now
        r = self.rfm9x
        # Additional 4 bytes added by the RFM9x library due to explicit header mode
        # Maximum payload size 252 + 4 bytes header = 256 bytes
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
        bands = self.dc_tracker.get_registered_bands()
        band, wait_time = BandSelect.select_band(
            bands,
            packet_time,
            packet.p_type,
            self.time_scale,
            self.formula_weights,
            self.temp,
            self.min_control_reserve_ratio,
            self.allow_wait_candidates,
            self.wait_horizon_sec,
            now,
        )
        sleep(wait_time)
        self.dc_tracker.validate_can_transmit(band.name, packet_time)
        frequency = self.channels.select_channel(band.name)

        # Annotation at @property frequency changed from Literal[433.0, 915.0] to float
        r.frequency_mhz = frequency

        self.apply_link_profile(
            7,
            125000,
            5,
            10,
            True,
        )

        # Annotation of ReadableBuffer explicity says 'Any' instead of being implied
        if packet.p_type == PacketType.CONFIRMABLE:
            setattr(r, "destination", packet.target)
            r.send_with_ack(packet.to_byte())
        else:
            r.send(packet.to_byte(), destination=packet.target, node=packet.source, flags=APP_ACK_REQ)

    def receive(self) -> "Optional[str]":
        r = self.rfm9x
        # Implement the ACK duty cycle tracker thing when receiving a packet. (look into ack flags again)
        packet_bytes = r.receive(with_header=True)

        message = packet_bytes.decode("utf-8") if packet_bytes is not None else packet_bytes
        return message
