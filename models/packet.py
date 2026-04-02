"""
Define Packet dataclass
"""
from models.packet_type import PacketKind, PacketKindType
from models.model import NodeID
from exceptions.packet.target_unspecified import TargetUnspecifiedError
from exceptions.packet.message_unspecified_error import MessageUnspecifiedError

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional


class Packet:
    """
    @dataclass
    Define packet structure and methods
    """
    __slots__ = (
        "source",
        "target",
        "p_type",
        "identifier",
        "message",
        )

    source: int
    target: "Optional[NodeID]"
    p_type: "PacketKindType"
    message: "Optional[str]"

    def __init__(
            self,
            source: int,
            target: "Optional[NodeID]",
            p_type: "PacketKindType",
            identifier: int,
            message: "Optional[str]",
        ) -> None:
        self.source       = source
        self.target       = target
        self.p_type       = p_type
        self.identifier   = identifier
        self.message      = message

    def validate_packet(self) -> None:
        """
        Checks if the packet has a target node set, 
        throws TargetUnspecifiedError if not present.

        Checks if the packet is of type 2 , a data packet,
        then it must contain a message, otherwise throws MessageUnspecifiedError.
        
        
        :param self: Packet instance
        :return: Returns True if the packet is valid, otherwise False.
        :rtype: bool
        """
        if self.target is None:
            raise TargetUnspecifiedError(self.source, self.p_type, self.message)

        if self.p_type == PacketKind.DATA and self.message is None:
            raise MessageUnspecifiedError(self.source, self.p_type, self.target)

    def to_byte(self) -> bytearray:
        """
        Returns bytearray of the parameter message.
        Format -> b'self.message'
        
        :param self: Packet instance
        :return: Returns bytearray of the message.
        :rtype: bytearray
        """
        self.validate_packet()
        msg = "" if self.message is None else self.message
        return bytearray(msg, "utf-8")
