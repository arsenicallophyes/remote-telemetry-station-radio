"""
Define Packet dataclass
"""
from typing import Optional
from dataclasses import dataclass

from Codebase.node.packet_type import PacketType
from Codebase.node.node        import Node

@dataclass
class Packet:
    """
    Define packet structure and methods
    """
    source: Node
    target: Optional[Node]
    type: PacketType
    message: Optional[str]

