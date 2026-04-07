import random
from time import monotonic, sleep, struct_time


from node.mixins.state import NodeState
from node.transport.peer import Peer
from node.transport.peer_table import PeerTable
from node.transport.types.sequence_response import SequenceResponse
from node.transport.types.retransmit_state import RetransmitState
from node.storage.persistance_manager import PersistenceManager
from node.protocol.parameters import validate_parameters, Parameters, ParametersType

from models.packet import Packet
from models.model import NodeID
from models.packet_type import PacketKind

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False  # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional, Set, Tuple, List
    from adafruit_rfm9x_patched import RFM9x
    from node.mac.band_airtime import WaitTime
    from models.model import SpreadingFactor, CodingRate, Frequency, Message, Identifier
    from regulations.types.model import Band

    from models.packet_type import PacketKindType
    from node.protocol.parameters import ParametersDict
    from node.mac.band_airtime import BandAirtime

ACK_MESSAGE  = "1"
NACK_IGNORE  = "IGNORE"


class ControlMixin(NodeState):
    rfm9x: "RFM9x"
    node_id:                  int
    peer_table:               PeerTable
    persistence_manager:      PersistenceManager

    ack_wait:                    float
    control_frequency:           float
    control_transmition_retries: int
    control_band:                "Band"
    spreading_factor:            "SpreadingFactor"
    bandwidth:                   int
    coding_rate:                 "CodingRate"
    wait_horizon_sec:            "WaitTime"

    if TYPE_CHECKING:
        # pylint: disable=unused-argument
        def apply_link_profile(
            self,
            sf: SpreadingFactor,
            bw: int,
            cr: CodingRate,
            tx_power_dbm: int,
            crc: bool = True,
            preamble: int = 8,
        ) -> None: ...

        def decode_packet(
            self,
            packet_bytes: bytearray,
        ) -> Tuple[Message, NodeID, Identifier, PacketKindType]: ...

        def acquire_channel(
            self,
            packet: Packet,
            now: "Optional[float]" = None,
        ) -> "Tuple[Frequency, BandAirtime, float]": ...

    def _control_transmit_nack(
        self,
        packet: Packet,
        peer: Peer,
        now: "Optional[float]" = None,
    ) -> "Optional[Set[int]]":
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
            self.acquire_channel(packet, now)
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

            message, _, _, packet_kind = self.decode_packet(packet_bytes) # pylint: disable=assignment-from-no-return
            message = str(message)

            if packet_kind != PacketKind.ACK:
                print("Ignoring packet", f"{message=}")
                continue

            if message == NACK_IGNORE:
                queued_packets: "Set[int]" = set()
            else:
                try:
                    queued_packets = set(int(i) for i in message.split(":"))
                except ValueError:
                    continue

            print(f"Ack Received {message=}")
            peer.transmit.increment_sequence()
            return queued_packets

    def control_transmit_ack(
        self,
        packet: Packet,
        peer: Peer,
        now: "Optional[float]" = None,
    ) -> "Optional[bool]":
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
            self.acquire_channel(packet, now)
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

            message, _, _, packet_kind = self.decode_packet(packet_bytes) # pylint: disable=assignment-from-no-return
            message = str(message)

            if packet_kind != PacketKind.ACK:
                print("Ignoring packet", f"{message=}")
                continue

            if not message.isdecimal():
                continue

            if message != ACK_MESSAGE:
                print("Wrong message", f"{message=}")
                continue

            print(f"Ack Received {message=}")
            peer.transmit.increment_sequence()
            return True

    def control_receive(
        self,
        expected_parameter: ParametersType,
        listen_window: "Optional[float]" = None,
    ) -> "Optional[ParametersDict]":
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

            message, source, _, packet_kind = self.decode_packet(packet_bytes) # pylint: disable=assignment-from-no-return

            if packet_kind != PacketKind.CONTROL:
                continue

            peer = self.peer_table.get_peer(source)

            if not peer:
                print(f"Unregistered peer: {source=}: {message}")
                continue

            parameters = validate_parameters(message) # pylint: disable=assignment-from-no-return

            if not parameters:
                continue

            timestamp = parameters.get(Parameters.TIMESTAMP)

            if not timestamp:
                continue

            if not isinstance(timestamp, struct_time):
                continue

            if not parameters.get(expected_parameter):
                continue
            
            ack_packet = Packet(
                self.node_id,
                source,
                PacketKind.ACK,
                peer.transmit.next_seq,
                "1",
            )

            self.acquire_channel(ack_packet) # pylint: disable=assignment-from-no-return
            r.send(
                ack_packet.to_byte(),
                destination=ack_packet.target,
                node=ack_packet.source,
                identifier=ack_packet.identifier,
                flags=ack_packet.p_type
            )
            peer.transmit.increment_sequence()

            return parameters


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
            PacketKind.NACK,
            peer.transmit.next_seq,
            message,
        )

        peer.receive.missed_packets = None
        queued_packets = self._control_transmit_nack(packet, peer, now)

        return queued_packets

    def control_listen_NACK(
        self,
        expected_source: NodeID,
        now: "Optional[float]" = None,
    ) -> None:
        now = monotonic() if now is None else now
        r = self.rfm9x

        packet_bytes = r.receive(with_header=True, timeout=self.ack_wait)

        if packet_bytes is None:
            return

        message, source, identifier, packet_kind = self.decode_packet(packet_bytes) # pylint: disable=assignment-from-no-return
        message = str(message)


        peer = self.peer_table.get_peer(expected_source)
        if not peer:
            return

        if expected_source != source:
            print("Send busy message if registered")
            return

        if packet_kind != PacketKind.NACK:
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
            if packet and packet.p_type == PacketKind.DATA:
                queued_packets.add(packet)
                queued_packets_identifiers.append(packet.identifier)

        if not queued_packets:
            message = NACK_IGNORE
        else:
            message = ":".join(str(i) for i in queued_packets_identifiers)

        NACK_ACK_packet = Packet(
            self.node_id,
            expected_source,
            PacketKind.ACK,
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
