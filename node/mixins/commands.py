from time import monotonic, sleep
import random

from models.packet import Packet
from models.packet_type import PacketKind
from models.model import NodeID, Identifier

from node.protocol.parameters import CommandParameters, add_parameter, add_timestamp
from node.transport.peer_table import PeerTable
from node.transport.types.authorization_state import AuthorizationState

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False  # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional, Tuple
    from rtc import RTC # pyright: ignore[reportMissingModuleSource] # pylint: disable=import-error
    from adafruit_rfm9x_patched import RFM9x
    from node.mac.band_airtime import WaitTime
    from models.model import SpreadingFactor, CodingRate, Frequency
    from node.transport.peer import Peer
    from node.protocol.parameters import ParametersDict
    from node.mac.band_airtime import BandAirtime



BROADCAST_ADDRESS = NodeID(255)
NETWORK_ID = b"\x0E\x1F\x7D\x2C"

class CommandsMixin:
    rfm9x:   "RFM9x"
    node_id: int
    rtc:     "RTC"

    spreading_factor: "SpreadingFactor"
    coding_rate:      "CodingRate"
    wait_horizon_sec: "WaitTime"
    bandwidth:         int
    ack_wait:          float
    peer_table:        PeerTable
    etx_packets_count: int

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

        def control_receive(
            self,
            deadline: float,
        ) -> Optional[Tuple[ParametersDict, NodeID, Optional[Peer]]]: ...

        def control_transmit_await_ack(
            self,
            packet: Packet,
            peer: Peer,
            now: Optional[float] = None,
        ) -> Optional[bool]: ...

        def control_send_ack(
            self,
            target: NodeID,
            peer: Optional[Peer] = None,
        ) -> None: ...

        def acquire_channel(
            self,
            packet: Packet,
            now: Optional[float] = None,
        ) -> Tuple[Frequency, BandAirtime, float]: ...

        def etx_receive(
                self,
                expected_source: NodeID,
                listen_window: Optional[float],
                now: Optional[float] = None,
            ) -> None: ...

        def etx_transmit(
            self,
            target: NodeID,
            now: Optional[float] = None,
        ) -> None: ...

        def etx_complete(
            self,
            peer: Peer,
            successfully_transmitted_packet: int,
        ) -> None: ...
        



    def network_join(
        self,
        listen_window: "Optional[float]",
        now: "Optional[float]" = None,
    ) -> None:
        now = monotonic() if now is None else now
        r = self.rfm9x

        message = add_parameter(None, CommandParameters.NETWORK_JOIN, NETWORK_ID.decode()) #  pylint: disable=assignment-from-no-return
        message = add_timestamp(self.rtc.datetime, message)

        packet = Packet(self.node_id, BROADCAST_ADDRESS, PacketKind.CONTROL, 0, message)
        self.acquire_channel(packet, now)
        r.send(
            packet.to_byte(),
            destination=packet.target,
            node=packet.source,
            identifier=packet.identifier,
            flags=packet.p_type
        )
        sleep(0.4)

        deadline = monotonic() + (listen_window if listen_window else float(self.wait_horizon_sec))

        while monotonic() < deadline:

            response = self.control_receive(deadline) # pylint: disable=assignment-from-no-return

            if not response:
                continue

            parameters, source, _ = response

            seq = parameters.get(CommandParameters.NETWORK_ACCEPT)

            if not isinstance(seq, int):
                continue

            seq = Identifier(seq)

            self.peer_table.add_peer(source, AuthorizationState.REGISTERED, seq)


    def network_accept(self, network_id: bytes, source: NodeID) -> None:
        if network_id != NETWORK_ID:
            return

        peer = self.peer_table.get_peer(source)

        if peer and peer.state == AuthorizationState.REGISTERED:
            return

        # Random sleep from 0.6 to 2.0s to prevent collision
        n = random.randint(1, 15) / 10 + self.ack_wait
        sleep(n)

        self.peer_table.add_peer(source, AuthorizationState.PENDING)

        peer = self.peer_table.get_peer(source)
        if not peer:
            return

        message = add_parameter(None, CommandParameters.NETWORK_ACCEPT, str(peer.transmit.next_seq))
        message = add_timestamp(self.rtc.datetime, message)


        packet = Packet(
            self.node_id,
            source,
            PacketKind.CONTROL,
            peer.transmit.next_seq,
            message,
        )

        response = self.control_transmit_await_ack(packet, peer) # pylint: disable=assignment-from-no-return

        if response:
            peer.state = AuthorizationState.REGISTERED

    def network_rejoin(self, peer: "Peer") -> None:

        message = add_parameter(None, CommandParameters.NETWORK_REJOIN)
        message = add_timestamp(self.rtc.datetime, message)

        packet = Packet(
            self.node_id,
            peer.node_id,
            PacketKind.CONTROL,
            peer.transmit.next_seq,
            message,
        )

        self.control_transmit_await_ack(packet, peer) # pylint: disable=assignment-from-no-return

    def benchmark_all_nodes_with_etx(self):
        peers = self.peer_table.peers
        for target, peer in peers.items():
            tx_first = target < self.node_id
            message = add_parameter(
                None,
                CommandParameters.START_ETX_RX if tx_first else CommandParameters.START_ETX_TX,
            )
            message = add_timestamp(self.rtc.datetime, message)
            packet = Packet(
                self.node_id,
                peer.node_id,
                PacketKind.CONTROL,
                peer.transmit.next_seq,
                message,
            )
            response = self.control_transmit_await_ack(packet, peer) # pylint: disable=assignment-from-no-return
            if not response:
                continue

            self.start_etx(target, peer, tx_first)

    def start_etx(self, target: NodeID, peer: "Peer", tx_first: bool):
        now = monotonic()
        if tx_first:
            self.etx_transmit(target, now)
            forwarded_packets = self.wait_for_etx_count(target, peer)
            self.etx_receive(target, self.wait_horizon_sec) # pylint: disable=assignment-from-no-return
            self.send_etx_count(peer)
        else:
            self.etx_receive(target, self.wait_horizon_sec) # pylint: disable=assignment-from-no-return
            self.send_etx_count(peer)
            self.etx_transmit(target, now)
            forwarded_packets = self.wait_for_etx_count(target, peer)

        if forwarded_packets:
            self.etx_complete(peer, forwarded_packets)

    def wait_for_etx_count(self, expected_source: NodeID, peer: "Peer") -> "Optional[int]":
        deadline = monotonic() + float(self.wait_horizon_sec)

        while monotonic() < deadline:
            response = self.control_receive(deadline) # pylint: disable=assignment-from-no-return

            if not response:
                continue

            parameters, source, _ = response

            if source != expected_source:
                continue

            result = parameters.get(CommandParameters.ETX_COUNT)

            if not isinstance(result, int):
                continue

            self.control_send_ack(source, peer)
            return result

    def send_etx_count(self, peer: "Peer"):
        message = add_parameter(None, CommandParameters.ETX_COUNT, str(peer.etx_rx_count))
        message = add_timestamp(self.rtc.datetime, message)

        packet = Packet(
            self.node_id,
            peer.node_id,
            PacketKind.CONTROL,
            peer.transmit.next_seq,
            message,
        )

        self.control_transmit_await_ack(packet, peer)
