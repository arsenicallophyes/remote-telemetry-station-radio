from time import struct_time


from node.transport.peer import Peer

from models.packet_type import PacketKindType
from models.model import Message, NodeID, Identifier

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False  # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional, Tuple
    from adafruit_rfm9x_patched import RFM9x
    from rtc import RTC # pyright: ignore[reportMissingModuleSource] # pylint: disable=import-error


class UtilsMixin:
    rfm9x: "RFM9x"
    rtc: "RTC"

    def decode_packet(
        self,
        packet_bytes: bytearray,
    ) -> "Tuple[Message, NodeID, Identifier, PacketKindType]":
        headers = packet_bytes[:4]
        message = Message(packet_bytes[4:].decode("utf-8"))

        source = NodeID(headers[1])
        identifier = Identifier(headers[2])
        packet_kind = PacketKindType(headers[3])

        return message, source, identifier, packet_kind

    def extract_timestamp(self, message: Message) -> "Optional[struct_time]":
        stamp  = message.split("_", 1)[0]
        parts = stamp.split(":")
        if len(parts) != 6:
            return

        try:
            y, mo, d, h, mi, s = (int(x) for x in parts)
        except ValueError:
            return None

        return struct_time((y, mo, d, h, mi, s, 0, 0, -1))

    def log_peer_activity(self, peer: Peer, identifier: int) -> None:
        r = self.rfm9x
        peer.receive.last_seen = self.rtc.datetime
        peer.receive.link_quality = float(r.last_rssi)
        peer.receive.last_seq = identifier
