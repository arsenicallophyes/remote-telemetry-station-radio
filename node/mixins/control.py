import random
from time import monotonic, sleep


from node.mixins.state import NodeState
from node.transport.peer import Peer
from node.transport.peer_table import PeerTable
from node.transport.types.sequence_response import SequenceResponse
from node.transport.types.retransmit_state import RetransmitState
from node.storage.persistance_manager import PersistenceManager

from models.packet import Packet
from models.model import NodeID
from models.packet_type import PacketKind

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False  # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional, Set, Tuple, Literal, Dict, List
    from adafruit_rfm9x_patched import RFM9x
    from node.mac.band_airtime import WaitTime
    from models.model import SpreadingFactor, CodingRate
    from regulations.types.model import Band

    from models.model import Message, Identifier
    from models.packet_type import PacketKindType

ACK_MESSAGE  = 1
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
    ) -> "Optional[Literal[1]]":
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

            message, _, _, packet_kind = self.decode_packet(packet_bytes) # pylint: disable=assignment-from-no-return
            message = str(message)

            if packet_kind != PacketKind.ACK:
                print("Ignoring packet", f"{message=}")
                continue

            if not message.isdecimal():
                continue
            message = int(message)

            if message != ACK_MESSAGE:
                print("Wrong message", f"{message=}")
                continue

            print(f"Ack Received {message=}")
            peer.transmit.increment_sequence()
            return message

    def control_receive(
        self,
        listen_window: "Optional[float]" = None,
    ) -> "Optional[float]":
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
            message = str(message)

            if packet_kind != PacketKind.CONTROL:
                continue

            peer = self.peer_table.get_peer(source)

            if not peer:
                print(f"Unregistered peer: {source=}: {message}")
                continue

            parameters: "Dict[str, float]" = {}
            args: "List[str]" = message.split(":")

            if len(args) % 2 != 0:
                print(f"Invalid paramters format: {message=}")
                continue

            try:
                for i in range(0, len(args), 2):
                    parameters[args[i]] = float(args[i+1])
            except IndexError:
                print(f"Index Error: {message=}")
                continue
            except KeyError:
                print(f"Key Error: {message=}")
                continue

            if not parameters:
                continue

            frequency   = parameters.get("DT")
            packet_time = parameters.get("PT")
            etx_count   = parameters.get("ET")

            if not etx_count or not (frequency and packet_time):
                continue

            r.send(
                b"1",
                destination=source,
                node=self.node_id,
                identifier=peer.transmit.next_seq,
                flags=PacketKind.ACK
            )
            peer.transmit.increment_sequence()
            sleep(0.15)
            if frequency and packet_time:
                r.frequency_mhz = frequency
                r.listen()
                return packet_time
            elif etx_count:
                return etx_count

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
