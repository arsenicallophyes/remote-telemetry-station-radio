"""
Define packet types via code
"""
try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Literal
    PacketCode = Literal[0, 1, 2, 3]
else:
    PacketCode = int


class PacketType:
    """
    Define a set of codes used to indicate the packet type.
    """
    CONTROL    : "PacketCode" = 0
    ACK        : "PacketCode" = 1
    DATA       : "PacketCode" = 2
    CONFIRMABLE: "PacketCode" = 3
