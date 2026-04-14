from node.node import Node
from regulations.EU863.bands import BANDS

BASE = False
NODE = False

if BASE and NODE:
    raise SystemError(f"Base and Node flags both set to true. {BASE=} {NODE=}")

if BASE:
    node = Node("Base", 0, 869.8, BANDS)
else:
    node = Node("A", 1, 869.8, BANDS)

node.run()
