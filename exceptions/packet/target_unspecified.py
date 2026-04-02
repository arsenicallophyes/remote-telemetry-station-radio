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

class TargetUnspecifiedError(PacketError):
    """
    Raised when the target node is not specified.
    """
    def __init__(self, source: int, p_type: PacketKindType, message: "Optional[str]") -> None:
        message = (
            f"Source {source} has not specified the target node. "
            f"Attempted to send a packet of type {p_type}, with message of "
            f"'{message}'"
        )
        super().__init__(message, code=201)
        self.source  = source
        self.type    = p_type
        self.message = message
