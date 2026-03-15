from node.node import Node
from regulations.EU863.bands import BANDS
from models.packet import Packet
from models.packet_type import PacketType
from time import sleep

source = 0
node = Node("Base", source, 863, BANDS)

packet = Packet(
    source, 1, PacketType.DATA, "Hello World."
)

while True:
    node.transmit(packet)
    sleep(2)
