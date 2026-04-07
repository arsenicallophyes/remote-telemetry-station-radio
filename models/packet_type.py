"""
Define packet types via code
"""
try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import NewType
    PacketKindType = NewType("PacketKindType", int)

else:
    PacketKindType = int

class PacketKind:
    """
    @enum
    Define a set of codes used to indicate the packet type.
    """
    CONTROL     = PacketKindType(0)
    ACK         = PacketKindType(1)
    DATA        = PacketKindType(2)
    CONFIRMABLE = PacketKindType(3)
    NACK        = PacketKindType(4)
