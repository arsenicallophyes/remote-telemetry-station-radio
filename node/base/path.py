"""
Define path object
"""
from node.base.types.node_type import NodeType

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import List
class Path:

    def __init__(self, nodes_list: "List[NodeType]", cost: float) -> None:
        self.path : "List[int]" = []
        self.nodes_list = nodes_list
        self.cost = cost
        for node in nodes_list:
            self.path.append(node.node_id)

    def __str__(self) -> str:
        return "->".join(str(n) for n in self.nodes_list) + f" | Cost: {self.cost}"
