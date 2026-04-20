from node.node import Node
from regulations.EU863.bands import BANDS

from node.base.routing_table import RoutingTable
from models.model import NodeID


BASE = False
A    = False
B    = False
C    = False

roles = BASE, A, B, C
if sum(roles) != 1:
    raise SystemError(f"Only a single flag can be True. {roles=}")

if BASE:
    node = Node("Base", 0, 869.8, BANDS)
elif A:
    node = Node("A", 1, 869.8, BANDS)
    table = RoutingTable(NodeID(1), NodeID(0))
    table.set_parents(parent=NodeID(0), backup=None)
    node.install_routing_table(table)
elif B:
    node = Node("B", 2, 869.8, BANDS)
    table = RoutingTable(NodeID(2), NodeID(0))
    table.set_parents(parent=NodeID(1), backup=NodeID(0))
    node.install_routing_table(table)
elif C:
    node = Node("C", 3, 869.8, BANDS)
    table = RoutingTable(NodeID(3), NodeID(0))
    table.set_parents(parent=NodeID(0), backup=NodeID(1))
    node.install_routing_table(table)
else:
    # Redundant Check (for mypy)
    raise SystemError(f"Only a single flag can be True. {roles=}")

node.run()
