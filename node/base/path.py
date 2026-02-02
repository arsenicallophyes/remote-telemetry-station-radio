"""
Define path object
"""
from typing import List
from uuid import UUID
from node.node import Node

class Path:

    def __init__(self, nodes_list: List[Node], cost: float) -> None:
        self.path : List[UUID] = []
        self.nodes_list = nodes_list
        self.cost = cost
        for node in nodes_list:
            self.path.append(node.node_id)

    def __str__(self) -> str:
        return "->".join(str(n) for n in self.nodes_list) + f" | Cost: {self.cost}"
