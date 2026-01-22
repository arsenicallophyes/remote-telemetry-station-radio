"""
Define object node
"""
from uuid import UUID
from Codebase.models.packet import Packet
from Codebase.node.packet_type import PacketType as pt


class Node:
    """
    Node class
    """
    def __init__(self, name: str, node_id: UUID) -> None:
        """
        @name:    str  -> Node's name
        @node_id: UUID -> Node's unique identifier
        """
        self.name      = name
        self.node_id   = node_id

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, value: object) -> bool:
        return value == self.name

    def __str__(self) -> str:
        return self.name

    def send(self, packet: Packet) -> None:
        print(packet)

    def receive(self) -> Packet:
        node = Node(self.name, self.node_id)
        packet = Packet(node, node, pt.ACK, "TEMP")
        return packet
