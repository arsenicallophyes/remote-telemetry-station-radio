"""
Define object node
"""
from time import monotonic, sleep, struct_time
import random
import rtc # pyright: ignore[reportMissingModuleSource] # pylint: disable=import-error


import board
import busio
import digitalio
from adafruit_rfm9x_patched import RFM9x

from node.transport.peer_table import PeerTable
from node.transport.peer import Peer
from node.transport.types.sequence_response import SequenceResponse
from node.transport.types.recovery_state import RecoveryState
from node.transport.types.retransmit_state import RetransmitState

from node.storage.persistance_manager import PersistenceManager

from node.mac.airtime import Airtime
from node.mac.band_airtime import WaitTime
from node.mac.duty_cycle_tracker import DutyCycleTracker
from node.mac.band_selection import BandSelect
from node.mac.channel_selection import ChannelSelect


from models.packet import Packet
from models.model import SpreadingFactor, CodingRate, NodeID
from models.packet_type import PacketType

from regulations.types.model import BandsSeq
from regulations.EU863.bands import BANDS

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional, Tuple, Dict, List, Literal, Set

# Adafruit RFM9X library does not support implicit
# header mode, thus spreading factor 6 is not supported.
# Spreading factor 6 requires an implicit header, as
# specified by the RFM95W Lora modem datasheet.
IMPLICIT_HEADER_MODE = False
ACK_MESSAGE = 1
NACK_IGNORE = "IGNORE"
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

    control_band = BANDS[5] # Band P
    control_transmition_retries = 5
    control_frequency = 869.8 # Must be 

    ack_wait = 0.5

    bandwidth = 125_000
    spreading_factor: "SpreadingFactor" = 7
    coding_rate: "CodingRate" = 5

    def __init__(self, name: str, node_id: int, freq: float, bands: BandsSeq) -> None:
        """
        Initialize class Node.

        :param name: Node's name
        :param node_id: Node's unique identifier
        """
        self.name      = name
        self.node_id   = node_id

        self.dc_tracker   = DutyCycleTracker()
        self.channels     = ChannelSelect(self.bandwidth)

        self.peer_table          = PeerTable()
        self.persistence_manager = PersistenceManager("/control", "/data")

        self.recovery     = None
        self.retransmit   = None

        self.__init_radio__(freq, bands)
        self.__init_rtc__()

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

    def control_transmit_nack(self, packet: Packet, peer: Peer, now: "Optional[float]" = None) -> "Optional[Set[int]]":
        now = monotonic() if now is None else now
        r = self.rfm9x

        self.apply_link_profile(
            self.spreading_factor,
            self.bandwidth,
            self.coding_rate,
            self.control_band.erp,
            True,
        )

        r.frequency_mhz = self.control_frequency

        n = 0
        while n < self.control_transmition_retries:
            n += 1
            r.send(
                packet.to_byte(),
                destination=packet.target,
                node=packet.source,
                identifier=packet.identifier,
                flags=packet.p_type
            )

            packet_bytes = r.receive(with_header=True, timeout=self.ack_wait)

            if packet_bytes is None:
                sleep(self.ack_wait + self.ack_wait * random.random())
                continue

            headers = packet_bytes[:4]
            message = packet_bytes[4:].decode("utf-8")

            packet_type = int(headers[3])
            if packet_type != PacketType.ACK:
                print("Ignoring packet", f"{headers=}:{message=}")
                continue

            if message == NACK_IGNORE:
                queued_packets: "Set[int]" = set()
            else:
                try:
                    queued_packets = set(int(i) for i in message.split(":"))
                except ValueError:
                    continue

            print(f"Ack Received {headers=}:{message=}")
            peer.transmit.increment_sequence()
            return queued_packets
    

    def control_transmit_ack(self, packet: Packet, peer: Peer, now: "Optional[float]" = None) -> "Optional[Literal[1]]":
        now = monotonic() if now is None else now
        r = self.rfm9x

        self.apply_link_profile(
            self.spreading_factor,
            self.bandwidth,
            self.coding_rate,
            self.control_band.erp,
            True,
        )

        r.frequency_mhz = self.control_frequency

        n = 0
        while n < self.control_transmition_retries:
            n += 1
            r.send(
                packet.to_byte(),
                destination=packet.target,
                node=packet.source,
                identifier=packet.identifier,
                flags=packet.p_type
            )

            packet_bytes = r.receive(with_header=True, timeout=self.ack_wait)

            if packet_bytes is None:
                sleep(self.ack_wait + self.ack_wait * random.random())
                continue

            headers = packet_bytes[:4]
            message = packet_bytes[4:].decode("utf-8")

            if not message.isdecimal():
                continue

            message = int(message)

            packet_type = int(headers[3])
            if packet_type != PacketType.ACK:
                print("Ignoring packet", f"{headers=}:{message=}")
                continue

            if message != ACK_MESSAGE:
                print("Wrong message", f"{headers=}:{message=}")
                continue

            print(f"Ack Received {headers=}:{message=}")
            peer.transmit.increment_sequence()
            return message


    def data_transmit(self, packet: Packet, now: "Optional[float]" = None) -> None:
        now = monotonic() if now is None else now
        r = self.rfm9x
        packet.validate_packet()

        # Packet.validate_packet() handles the verification process
        # This if statement is done for the IDE type checker
        # Thus, this statement never returns
        if packet.target is None:
            return

        peer = self.peer_table.get_peer(packet.target)
        if peer is None:
            print("Peer Unregistered")
            return

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
        control_packet = Packet(
            self.node_id,
            packet.target,
            PacketType.CONTROL,
            peer.transmit.next_seq,
            f"DT:{frequency}:PT:{packet_time}"
        )
        if not self.control_transmit_ack(control_packet, peer, now):
            print("Receiver unresponsive")
            return

        # Annotation at @property frequency changed from Literal[433.0, 915.0] to float
        sleep(0.15)
        r.frequency_mhz = frequency

        self.apply_link_profile(
            self.spreading_factor,
            self.bandwidth,
            self.coding_rate,
            10,
            True,
        )

        r.send(
            packet.to_byte(),
            destination=packet.target,
            node=packet.source,
            identifier=peer.transmit.next_seq,
            flags=packet.p_type,
        )
        peer.transmit.increment_sequence()
        self.dc_tracker.commit_airtime(band.name, packet_time)

        r.frequency_mhz = self.control_frequency

        if not self.retransmit:
            self.control_listen_NACK(packet.target, now)

    def control_receive(self, listen_window: "Optional[float]" = None) -> "Optional[float]":
        r = self.rfm9x
        r.frequency_mhz = self.control_frequency

        self.apply_link_profile(
            self.spreading_factor,
            self.bandwidth,
            self.coding_rate,
            self.control_band.erp,
            True,
        )
        deadline = monotonic() + (listen_window if listen_window else float(self.wait_horizon_sec))
        while monotonic() < deadline:

            packet_bytes = r.receive(with_header=True, timeout=self.ack_wait)
            if packet_bytes is None:
                print("Failed to get control packet")
                continue

            headers = packet_bytes[:4]
            message = packet_bytes[4:].decode("utf-8")

            packet_type = int(headers[3])
            if packet_type != PacketType.CONTROL:
                continue

            source = NodeID(headers[1])
            peer = self.peer_table.get_peer(source)

            if not peer:
                print(f"Unregistered peer: {source=}: {headers=}: {message}")
                continue

            parameters: "Dict[str, float]" = {}
            args: "List[str]" = message.split(":")

            if len(args) % 2 != 0:
                print(f"Invalid paramters format: {headers=}, {message=}")
                continue

            try:
                for i in range(0, len(args), 2):
                    parameters[args[i]] = float(args[i+1])

                frequency = parameters["DT"]
                packet_time = parameters["PT"]
            except IndexError:
                print(f"Index Error: {message=}")
                continue
            except KeyError:
                print(f"Key Error: {message=}")
                continue

            r.send(
                b"1",
                destination=source,
                node=self.node_id,
                identifier=peer.transmit.next_seq,
                flags=PacketType.ACK
            )
            peer.transmit.increment_sequence()
            sleep(0.15)
            r.frequency_mhz = frequency
            r.listen()
            return packet_time

    def data_receive(
            self,
            recovery_source: "Optional[NodeID]" = None,
            now: "Optional[float]" = None,
        ) -> "Optional[str]":
        now = monotonic() if now is None else now
        r = self.rfm9x
        try:
            packet_time = self.control_receive(listen_window=float(self.wait_horizon_sec))
            if not packet_time:
                return

            timeout = 2 * packet_time + self.ack_wait

            packet_bytes = r.receive(with_header=True, timeout=timeout)

            if packet_bytes is None:
                return

            headers = packet_bytes[:4]
            message = packet_bytes[4:].decode("utf-8")

            source = NodeID(headers[1])
            identifier = int(headers[2])
            packet_type = int(headers[3])

            if recovery_source and recovery_source != source:
                return

            if packet_type != PacketType.DATA:
                return

            timestamp = self.extract_timestamp(message)
            if not timestamp:
                return

            if not self.recovery:
                response = self.peer_table.handle_sequence(source, identifier)
            else:
                response = self.peer_table.handle_sequence_recovery(
                    source,
                    identifier,
                    self.recovery,
                )

                if response == SequenceResponse.ABORT:
                    return

            if response == SequenceResponse.UNREGISTERED:
                return

            peer = self.peer_table.get_peer(source)

            if not peer:
                return

            if response == SequenceResponse.DUPLICATE:
                self.log_peer_activity(peer, identifier)
                return

            if response == SequenceResponse.SUCCESS:
                self.log_peer_activity(peer, identifier)
                print(f"Saving -> {headers=}:{message=}:{timestamp=}")

            if response == SequenceResponse.AHEAD:
                nack_response = self.control_send_NACK(source, now)
                if nack_response is not None:
                    if len(nack_response) == 0:
                        peer.receive.set_sequence(identifier)
                        peer.receive.increment_sequence()
                    else:
                        self.recovery = RecoveryState(source, nack_response, identifier)
                self.log_peer_activity(peer, identifier)
                print(f"Saving -> {headers=}:{message=}:{timestamp=}")

            print(f"{headers=}:{message=}")
            return message
        finally:
            r.frequency_mhz = self.control_frequency

    def control_send_NACK(
            self,
            source: NodeID,
            now: "Optional[float]" = None
    ) -> "Optional[Set[int]]":
        now = monotonic() if now is None else now

        peer = self.peer_table.get_peer(source)

        if not peer:
            return

        missed_packets = peer.receive.missed_packets

        if not missed_packets:
            return

        message = ":".join(str(i) for i in missed_packets)
        packet = Packet(
            self.node_id,
            source,
            PacketType.NACK,
            peer.transmit.next_seq,
            message,
        )

        peer.receive.missed_packets = None
        queued_packets = self.control_transmit_nack(packet, peer, now)

        return queued_packets

    def data_recovery(self, listen_window: float, now: "Optional[float]" = None):
        if not self.recovery:
            return

        now = monotonic() if now is None else now

        source = self.recovery.source
        deadline = monotonic() + (listen_window if listen_window else float(self.wait_horizon_sec))

        while self.recovery.queued_packets:
            self.data_receive(source, now)
            if monotonic() > deadline:
                break

        if not self.recovery.queued_packets:
            peer = self.peer_table.get_peer(source)

            if not peer:
                return

            peer.receive.complete_recovery(self.recovery.ahead_seq)

        self.recovery = None

    def data_retransmission(self, now: "Optional[float]" = None):
        if not self.retransmit:
            return
        now = monotonic() if now is None else now

        for packet in self.retransmit.queued_packets:
            self.data_transmit(packet, now)

        self.retransmit = None

    def control_listen_NACK(self, expected_source: NodeID, now: "Optional[float]" = None):
        now = monotonic() if now is None else now
        r = self.rfm9x

        packet_bytes = r.receive(with_header=True, timeout=self.ack_wait)

        if packet_bytes is None:
            return

        headers = packet_bytes[:4]
        message = packet_bytes[4:].decode("utf-8")

        source = NodeID(headers[1])
        identifier = int(headers[2])
        packet_type = int(headers[3])

        peer = self.peer_table.get_peer(expected_source)
        if not peer:
            return

        if expected_source != source:
            print("Send busy message if registered")
            return

        if packet_type != PacketType.NACK:
            return

        response = self.peer_table.handle_sequence(source, identifier)

        if response != SequenceResponse.SUCCESS:
            return

        try:
            missed_packets = tuple(int(i) for i in message.split(":"))
        except ValueError:
            return

        queued_packets: "Set[Packet]" = set()
        queued_packets_identifiers: "List[int]" = []
        for i in missed_packets:
            packet = self.persistence_manager.retrieve_packet(i)
            if packet and packet.p_type == PacketType.DATA:
                queued_packets.add(packet)
                queued_packets_identifiers.append(packet.identifier)

        if not queued_packets:
            message = NACK_IGNORE
        else:
            message = ":".join(str(i) for i in queued_packets_identifiers)

        NACK_ACK_packet = Packet(
            self.node_id,
            expected_source,
            PacketType.ACK,
            peer.transmit.next_seq,
            message,
        )

        r.send(
            NACK_ACK_packet.to_byte(),
            destination=NACK_ACK_packet.target,
            node=NACK_ACK_packet.source,
            identifier=NACK_ACK_packet.identifier,
            flags=NACK_ACK_packet.p_type
        )
        peer.transmit.increment_sequence()
        self.retransmit = RetransmitState(expected_source, queued_packets)

    def log_peer_activity(self, peer: Peer, identifier: int) -> None:
        r = self.rfm9x
        peer.receive.last_seen = self.rtc.datetime
        peer.receive.link_quality = float(r.last_rssi)
        peer.receive.last_seq = identifier

    def extract_timestamp(self, message: str) -> "Optional[struct_time]":
        stamp  = message.split("_", 1)[0]
        parts = stamp .split(":")
        if len(parts) != 6:
            return

        try:
            y, mo, d, h, mi, s = (int(x) for x in parts)
        except ValueError:
            return None

        return struct_time((y, mo, d, h, mi, s, 0, 0, -1))
