"""
Define node startup behavior
"""
from Codebase.models.region import Region
from Codebase.models.band   import Band
from Codebase.models.packet import Packet

from Codebase.node.node              import Node
from Codebase.node.packet_type       import PacketType as pt
from Codebase.node.utils.band_helper import BandHelper

class Startup:
    """
    Define node startup behavior
    """
    def __init__(self, cmdf: float, region: Region, band: Band, node: Node) -> None:
        Region.validate(region)
        Band.validate(band)
        BandHelper(region, band).validate(cmdf)
        self.node = node

    def create_broadcast_packet(self) -> Packet:
        """
        Return broadcast packet
        """
        return Packet(self.node, None, pt.CONTROL, None)

    def broadcast(self) -> None:
        packet = self.create_broadcast_packet()
        self.node.send(packet)

if __name__ == "__main__":
    from uuid import uuid4
    Startup(433.175, Region.EU, Band.EU433, Node("A", uuid4()))
