"""
Define node startup behavior
"""
from node.node import Node

from models.packet import Packet
from models.packet_type import PacketType as pt

class Startup:
    """
    Define node startup behavior
    """
    def __init__(self, node: Node) -> None:
        self.node = node

    def create_broadcast_packet(self) -> Packet:
        """
        Return broadcast packet
        """
        return Packet(1, None, pt.CONTROL, None)

    def broadcast(self) -> None:
        packet = self.create_broadcast_packet()
        self.node.transmit(packet)
    

if __name__ == "__main__":
    pass
    # from uuid import uuid4
    # Startup(433.175, Region.EU, Band.EU433, Node("A", uuid4()))
