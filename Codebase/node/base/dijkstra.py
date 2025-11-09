"""
Dijkstra's Algorithm
"""
from typing import List, Set, Optional, Dict, Tuple
from uuid import uuid4, UUID
from Codebase.models.node import Node
from Codebase.models.path import Path


class Graph:
    """
    Class defining graph used for Dijkstra's algorithm
    """

    def __init__(self, size: int) -> None:
        self.size = size
        self.nodes_index: Dict[str, int] = {}
        self.nodes:    List[Node] = []
        self.node_ids: Set[UUID]  = set()

        self.connections_matrix: List[List[float]] = [[0.0] * size for _ in range(size)]

        self.init_base()

    def init_base(self):
        """
        Initialize BASE. Private method, do not run.
        """
        self.base       = self.add_node("BASE")
        self.base_index = 0

    def add_edge(self, node_a: str, node_b: str, weight: float) -> None:
        """
        Add edge to the connections matrix
        """
        u = self.nodes_index[node_a]
        v = self.nodes_index[node_b]
        if 0 <= u < self.size and 0 <= v and self.size:
            self.connections_matrix[u][v] = weight
            self.connections_matrix[v][u] = weight

    def add_node(self, name: str) -> Node:
        """
        Create a Node object with the assigned name
        
        @name: str

        Returns Node object
        """
        uuid = self.generate_id()
        self.node_ids.add(uuid)
        node = Node(name, uuid)
        self.nodes.append(node)
        self.nodes_index[name] = len(self.nodes) - 1
        return node

    def generate_id(self) -> UUID:
        """
        Ensures returned identifier is not being used by a different node.

        Most cases the loop is unenecassry, as chances of collision are near impossible.

        However, conceptually this is more robust.
        """
        while (uuid:= uuid4()) in self.node_ids:
            pass

        return uuid

    def dijkstra(self) -> Tuple[List[float], List[Optional[int]]]:
        """
        @node: Node must be the Base Station node.

        Returns the shortest distance from the Base Station to every node in the network.
        """

        distances:    List[float]         = [float("inf")] * self.size
        predecessors: List[Optional[int]] = [None] * self.size
        visited:      List[bool]          = [False] * self.size

        distances[self.base_index] = 0

        for _ in range(self.size):
            min_dist = float("inf")
            closest_node: Optional[int] = None
            for node_index in range(self.size):
                if not visited[node_index] and distances[node_index] < min_dist:
                    min_dist = distances[node_index]
                    closest_node = node_index

            if closest_node is None:
                break

            visited[closest_node] = True

            for neighbour_node in range(self.size):
                if self.connections_matrix[closest_node][neighbour_node] != 0 and not visited[neighbour_node]:
                    alternative_path = distances[closest_node] + self.connections_matrix[closest_node][neighbour_node]
                    if alternative_path < distances[neighbour_node]:
                        distances[neighbour_node]    = alternative_path
                        predecessors[neighbour_node] = closest_node

        return distances, predecessors

    def get_path(self, predecessors: List[Optional[int]], target_node: str, cost: float) -> Path:
        """
        @predecessors: A list of the predecessors node's indexes.

        @target_node:  The target node to reach from BASE.

        @cost:         The cost of the path.

        returns Path object
        """
        path: List[Node] = []
        current = self.nodes_index[target_node]

        while current is not None:
            path.insert(0, self.nodes[current])
            current = predecessors[current]
            if current == self.base_index:
                path.insert(0, self.base)
                break

        return Path(path, cost)

    def get_all_paths(self) -> List[Path]:
        """
        Runs Graph.get_path() on all registered nodes.

        Returns a List[Path] for all nodes.
        """
        distances, predecessors = self.dijkstra()
        paths: List[Path] = []

        for i, cost in enumerate(distances):
            path = self.get_path(predecessors, self.nodes[i].name, cost)
            paths.append(path)

        return paths

if __name__ == "__main__":
    graph = Graph(4)

    graph.add_node("B")
    graph.add_node("C")
    graph.add_node("D")

    graph.add_edge("BASE", "B", 1)
    graph.add_edge("BASE", "C", 3)

    graph.add_edge("B", "C", 1)
    graph.add_edge("B", "D", 5)
    graph.add_edge("C", "D", 2)

    # paths = graph.get_all_paths()

    # for path in paths:
    #     print(path)
