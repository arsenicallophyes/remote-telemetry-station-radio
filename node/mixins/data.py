from time import monotonic

from node.mixins.state import NodeState
from node.transport.peer_table import PeerTable
from node.transport.types.sequence_response import SequenceResponse
from node.transport.types.recovery_state import RecoveryState
from node.storage.persistance_manager import PersistenceManager
from node.protocol.parameters import add_parameter, Parameters

from models.packet import Packet
from models.packet_type import PacketKind
from models.model import NodeID

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False  # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional, Tuple, Set
    from time import struct_time

    from adafruit_rfm9x_patched import RFM9x

    from node.mac.band_airtime import WaitTime
    from node.mac.duty_cycle_tracker import DutyCycleTracker
    from node.mac.channel_selection import ChannelSelect
    from node.mac.band_airtime import BandAirtime

    from node.transport.peer import Peer

    from node.protocol.parameters import ParametersDict, ParametersType

    from models.model import SpreadingFactor, CodingRate, Message, Identifier, Frequency
    from models.packet_type import PacketKindType



class DataMixin(NodeState):
    rfm9x:               "RFM9x"
    node_id:             int
    peer_table:          PeerTable
    persistence_manager: PersistenceManager
    dc_tracker:          "DutyCycleTracker"
    channels:            "ChannelSelect"

    ack_wait:                float
    control_frequency:       float
    bandwidth:               int
    coding_rate:             "CodingRate"
    spreading_factor:        "SpreadingFactor"
    wait_horizon_sec:        "WaitTime"


    if TYPE_CHECKING:
        # pylint: disable=unused-argument
        def _control_transmit_nack(
            self,
            packet: Packet,
            peer: Peer,
            now: Optional[float] = None,
        ) -> Optional[Set[int]]: ...

        def control_transmit_ack(
            self,
            packet: Packet,
            peer: Peer,
            now: Optional[float] = None,
        ) -> Optional[bool]: ...

        def control_receive(
            self,
            expected_parameter: ParametersType,
            listen_window: Optional[float] = None,
        ) -> Optional[ParametersDict]: ...

        def control_send_NACK(
            self,
            source: NodeID,
            now: Optional[float] = None
        ) -> Optional[Set[int]]: ...

        def control_listen_NACK(
            self,
            expected_source: NodeID,
            now: Optional[float] = None,
        ) -> None: ...

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

        def extract_timestamp(
            self,
            message: Message,
        ) -> Optional[struct_time]: ...

        def log_peer_activity(
            self,
            peer: Peer,
            identifier: int,
        ) -> None: ...

        def acquire_channel(
            self,
            packet: Packet,
            now: Optional[float] = None,
        ) -> Tuple[Frequency, BandAirtime, float]: ...

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

        frequency, band, packet_time = self.acquire_channel(packet, now) # pylint: disable=assignment-from-no-return
        arguments = str(frequency), str(packet_time)
        message = add_parameter(None, Parameters.FREQUENCY_SWITCH, *arguments)

        control_packet = Packet(
            self.node_id,
            packet.target,
            PacketKind.CONTROL,
            peer.transmit.next_seq,
            message,
        )

        if not self.control_transmit_ack(control_packet, peer, now):
            print("Receiver unresponsive")
            return

        r.frequency_mhz = frequency

        self.apply_link_profile( # pylint: disable=assignment-from-no-return
            self.spreading_factor,
            self.bandwidth,
            self.coding_rate,
            25,
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

    def data_receive(
            self,
            recovery_source: "Optional[NodeID]" = None,
            now: "Optional[float]" = None,
        ) -> "Optional[str]":

        now = monotonic() if now is None else now
        r = self.rfm9x

        parameters = self.control_receive( # pylint: disable=assignment-from-no-return
            Parameters.FREQUENCY_SWITCH,
            listen_window=float(self.wait_horizon_sec),
        )

        if not parameters:
            return

        frequency, packet_time = parameters[Parameters.FREQUENCY_SWITCH]

        if not (isinstance(frequency, float) and isinstance(packet_time, float)):
            return

        r.frequency_mhz = frequency
        timeout = 2 * packet_time + self.ack_wait

        try:

            packet_bytes = r.receive(with_header=True, timeout=timeout)

            if packet_bytes is None:
                return

            message, source, identifier, packet_kind = self.decode_packet(packet_bytes) # pylint: disable=assignment-from-no-return

            if recovery_source and recovery_source != source:
                return

            if packet_kind != PacketKind.DATA:
                return

            timestamp = self.extract_timestamp(message) # pylint: disable=assignment-from-no-return
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
                print(f"Saving -> {message=}:{timestamp=}")

            if response == SequenceResponse.AHEAD:
                nack_response = self.control_send_NACK(source, now) # pylint: disable=assignment-from-no-return
                if nack_response is not None:
                    if len(nack_response) == 0:
                        peer.receive.set_sequence(identifier)
                        peer.receive.increment_sequence()
                    else:
                        self.recovery = RecoveryState(source, nack_response, identifier)
                self.log_peer_activity(peer, identifier)
                print(f"Saving -> {message=}:{timestamp=}")

            print(f"{message=}")
            return message
        finally:
            r.frequency_mhz = self.control_frequency

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
