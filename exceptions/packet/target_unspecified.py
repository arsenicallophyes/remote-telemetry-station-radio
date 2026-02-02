"""
Define custom error for exceeding permitted power usage.
"""
from exceptions.packet.packet_error import PacketError
from models.packet import Packet

class TargetUnspecifiedError(PacketError):
    """
    Raised when the target node is not specified.
    """
    def __init__(self, packet: Packet) -> None:
        message = (
            f"Source {packet.source.node_id} has not specified the target node. "
            f"Attempted to send a packet of type {packet.type}, with message of "
            f"'{packet.message}'"
        )
        super().__init__(message, code=201)
        self.source = packet.source
        self.type = packet.type
        self.message = packet.message
