"""
Define Packet dataclass
"""
from typing import Optional
from dataclasses import dataclass

from models.packet_type import PacketType
from node.node          import Node

@dataclass
class Packet:
    """
    Define packet structure and methods
    """
    source: Node
    target: Optional[Node]
    type: PacketType
    message: Optional[str]

    def validate_packet(self) -> bool:
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
            return False
        
        if self.type == 2 and self.message is None:
            return False
        
        return True

    def to_byte(self) -> bytearray:
        """
        Returns bytearray of all parameters concatenated by a colon.
        Format -> source:target:type:message
        
        :param self: Packet instance
        :return: Returns bytearray of the packet.
        :rtype: bytearray
        """
        msg = f"{self.source}:{self.target}:{self.type}:{self.message}"
        return bytearray(msg, "utf-8")
