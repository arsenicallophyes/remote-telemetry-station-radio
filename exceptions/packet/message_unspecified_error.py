"""
Define custom error for exceeding permitted power usage.
"""
from exceptions.packet.packet_error import PacketError
from models.packet import PacketKindType

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional

class MessageUnspecifiedError(PacketError):
    """
    Raised when the message parameter is not specified, under specific conditions.
    """
    def __init__(self, source: int, p_type: PacketKindType, target: "Optional[int]") -> None:
        message = (
            f"Source {source} attempted to send a type {p_type} packet to "
            f"{target} without providing a message."
        )
        super().__init__(message, code=202)
        self.source = source
        self.type =   p_type
        self.target = target
