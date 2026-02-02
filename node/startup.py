"""
Define node startup behavior
"""
from node.node              import Node
from node.utils.types.region import Region
from node.utils.types.band   import Band
from node.utils.band_helper import BandHelper

from models.packet import Packet
from models.packet_type       import PacketType as pt

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
    pass
    # from uuid import uuid4
    # Startup(433.175, Region.EU, Band.EU433, Node("A", uuid4()))
