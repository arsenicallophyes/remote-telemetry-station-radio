"""
Define packet types via code
"""
from enum import Enum

class PacketType(int, Enum):
    """
    Define a set of codes used to indicate the packet type.
    """
    CONTROL     = 0
    ACK         = 1
    DATA        = 2
    CONFIRMABLE = 3
