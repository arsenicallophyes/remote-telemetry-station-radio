from time import monotonic, sleep

from node.transport.peer_table import PeerTable
from node.protocol.parameters import Parameters

from models.packet import Packet
from models.packet_type import PacketKind, PacketKindType
from models.model import NodeID

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False  # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional, Tuple
    from adafruit_rfm9x_patched import RFM9x
    from node.mac.band_airtime import WaitTime
    from node.transport.peer import Peer
    from models.model import SpreadingFactor, CodingRate, Message, Identifier
    from regulations.types.model import Band
    from node.protocol.parameters import ParametersDict, ParametersType

ETX_MESSAGE = 0

class EtxMixin:
    rfm9x: "RFM9x"
    node_id: int
    peer_table: PeerTable

    etx_packets_count = 20
    spreading_factor: "SpreadingFactor"
    bandwidth: int
    coding_rate: "CodingRate"
    control_band: "Band"
    control_frequency: float
    wait_horizon_sec: "WaitTime"

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
            expected_parameter: ParametersType,
            listen_window: Optional[float] = None,
        ) -> Optional[Tuple[ParametersDict, NodeID]]:...

        def control_transmit_await_ack(
            self,
            packet: Packet,
            peer: Peer,
            now: Optional[float] = None,
        ) -> Optional[bool]: ...

        def decode_packet(
                self,
                packet_bytes: bytearray,
            ) -> Tuple[Message, NodeID, Identifier, PacketKindType]: ...

    def etx_transmit(
        self,
        target: "NodeID",
        now: "Optional[float]" = None,
    ) -> "Optional[int]":
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

        packet = Packet(self.node_id, target, PacketKind.CONTROL, 0, str(ETX_MESSAGE))
        for i in range(self.etx_packets_count):
            r.send(
                packet.to_byte(),
                destination=packet.target,
                node=packet.source,
                identifier=i,
                flags=packet.p_type
            )
            sleep(0.25)

        response = self.control_receive( # pylint: disable=assignment-from-no-return
            Parameters.ETX_COUNT,
            listen_window=self.wait_horizon_sec,
        )
        if not response:
            return

        parameters, _ = response

        received_packets = parameters[Parameters.ETX_COUNT]

        if not isinstance(received_packets, int):
            return

        return received_packets

    def etx_receive(
            self,
            expected_source: "NodeID",
            listen_window: "Optional[float]",
            now: "Optional[float]" = None,
        ) -> "Optional[int]":
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

        peer = self.peer_table.get_peer(expected_source)

        if not peer:
            return

        n = 0
        last_received = None
        deadline = monotonic() + (listen_window if listen_window else float(self.wait_horizon_sec))

        while n < self.etx_packets_count and monotonic() < deadline:
            packet_bytes = r.receive(with_header=True)

            if not packet_bytes:
                continue

            message, source, identifier, packet_kind = self.decode_packet(packet_bytes) # pylint: disable=assignment-from-no-return

            if source != expected_source:
                continue

            if packet_kind != PacketKind.CONTROL:
                continue

            if message != str(ETX_MESSAGE):
                continue

            n += 1
            last_received = identifier
            if last_received >= self.etx_packets_count:
                break

        packet = Packet(self.node_id, expected_source, PacketKind.CONTROL, 0, f"ET:{n}")

        response = self.control_transmit_await_ack(packet, peer, now) # pylint: disable=assignment-from-no-return

        if not response:
            return

        return n
