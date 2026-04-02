from time import sleep
import random

from node.node import Node
from regulations.EU863.bands import BANDS
from models.packet import Packet
from models.packet_type import PacketKind
from models.model import NodeID

words = (
    "Testing",
    "Infinite Chickens",
    "no",
    "Cows go moo",
    "LoRa sounds like a nice project, right? right??",
    "Behind you!",
    )

TRANSMIT = False
RECEIVE = False
if TRANSMIT:
    source = 0
    target = 1
    node = Node("Base", source, 869.8, BANDS)

    node.peer_table.add_peer(NodeID(target))
    packet = Packet(
        source, NodeID(target), PacketKind.DATA, 0, "Hello World."
    )

    while True:
        node.data_transmit(packet)
        index = random.randint(0, len(words) -1)
        packet.message = words[index]
        sleep(2)

if RECEIVE:
    source = 1
    target = 0
    node = Node("A", source, 869.8, BANDS)
    node.peer_table.add_peer(NodeID(target))
    while True:
        node.data_receive()
