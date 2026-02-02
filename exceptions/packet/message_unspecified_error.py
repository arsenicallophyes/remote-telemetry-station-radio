"""
Define custom error for exceeding permitted power usage.
"""
from exceptions.packet.packet_error import PacketError
from models.packet import Packet

class MessageUnspecifiedError(PacketError):
    """
    Raised when the message parameter is not specified, under specific conditions.
    """
    def __init__(self, packet: Packet) -> None:
        message = (
            f"Source {packet.source.node_id} attempted to send a type {packet.type} packet to "
            f"{packet.target} without providing a message."
        )
        super().__init__(message, code=202)
        self.source = packet.source
        self.type = packet.type
        self.target = packet.target
