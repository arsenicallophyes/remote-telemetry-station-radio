"""
Dijkstra's Algorithm
"""
from node.base.types.node_type import NodeType
from node.base.path import Path
from node.base.routing_table import RoutingTable

from models.model import NodeID

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import List, Set, Optional, Dict, Tuple

class Graph:
    """
    Class defining graph used for Dijkstra's algorithm
    """

    def __init__(self) -> None:
        self.size = 0
        self.nodes_index: "Dict[str, int]" = {}
        self.nodes:       "List[NodeType]" = []
        self.node_ids:    "Set[NodeID]"       = set()

        self.connections_matrix: "List[List[float]]" = [[0.0] * self.size for _ in range(self.size)]

        self.init_base()

    def init_base(self):
        """
        Initialize BASE. Private method, do not run.
        """
        self.base       = self.add_node("BASE", NodeID(0))
        self.base_index = 0

    def add_edge(self, node_a: str, node_b: str, weight: float) -> None:
        """
        Add edge to the connections matrix
        """
        u = self.nodes_index[node_a]
        v = self.nodes_index[node_b]

        if 0 <= u < self.size and 0 <= v <   self.size:
            self.connections_matrix[u][v] = weight
            self.connections_matrix[v][u] = weight

    def add_node(self, name: str, node_id: NodeID) -> NodeType:
        """
        Create a Node object with the assigned name
        
        @name: str

        Returns Node object
        """
        if node_id in self.node_ids:
            index = self.nodes_index[name]
            return self.nodes[index]
        self.expand_connection_matrix()

        self.node_ids.add(node_id)
        node = NodeType(name, node_id)
        self.nodes.append(node)
        self.nodes_index[name] = len(self.nodes) - 1
        return node

    def expand_connection_matrix(self) -> None:
        self.size += 1
        for row in self.connections_matrix:
            row.append(0.0)

        self.connections_matrix.append([0.0] * self.size)



    def dijkstra(self) -> "Tuple[List[float], List[Optional[int]]]":
        """
        @node: Node must be the Base Station node.

        Returns the shortest distance from the Base Station to every node in the network.
        """

        distances:    "List[float]"         = [float("inf")] * self.size
        predecessors: "List[Optional[int]]" = [None] * self.size
        visited:      "List[bool]"          = [False] * self.size

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

    def calculate_backup_parents(
        self,
        primary_predecessors: "List[Optional[int]]",
    ) -> "List[Optional[int]]":
        """
        Temporarily set the edge between the node considered
        and its parent to 0.0, re-run Dikstra's algorithm, fetch
        the new node, and set it as the backup.
        Afterwards, reset the edge to its original value.
        """

        backup_parents: "List[Optional[int]]" = [None] * self.size

        for node_index in range(self.size):
            if node_index == self.base_index:
                continue

            primary_parent = primary_predecessors[node_index]

            # If the node is unreachable, ignore, can't compute backup
            if primary_parent is None:
                continue

            # Fetch original weight and set edge to 0.0
            original_weight = self.connections_matrix[node_index][primary_parent]
            self.connections_matrix[node_index][primary_parent] = 0.0
            self.connections_matrix[primary_parent][node_index] = 0.0

            # Calculate alternative path
            _, alt_predecessors = self.dijkstra()
            backup_parents[node_index] = alt_predecessors[node_index]

            # Reset to original weight
            self.connections_matrix[node_index][primary_parent] = original_weight
            self.connections_matrix[primary_parent][node_index] = original_weight

        return backup_parents


    def build_routing_table(self) -> "Dict[NodeID, RoutingTable]":
        """
        Build routing table for each node
        """
        _, predecessors = self.dijkstra()
        backup_parents  = self.calculate_backup_parents(predecessors)

        base_id = self.nodes[self.base_index].node_id
        tables : "Dict[NodeID, RoutingTable]" = {}

        for node in self.nodes:
            tables[node.node_id] = RoutingTable(node.node_id, base_id)

        for i in range(self.size):
            if i == self.base_index:
                continue

            primary_index = predecessors[i]
            backup_index  = backup_parents[i]

            primary_id: "Optional[NodeID]" = self.nodes[primary_index].node_id if primary_index is not None else None
            backup_id:  "Optional[NodeID]" = self.nodes[backup_index].node_id  if backup_index  is not None else None

            tables[self.nodes[i].node_id].set_parents(primary_id, backup_id)

        for i in range(self.size):
            if i == self.base_index or predecessors[i] is None:
                continue

            destination_id: NodeID = self.nodes[i].node_id
            current = i
            parent  = predecessors[current]

            while parent is not None:
                ancestor_id:  NodeID = self.nodes[parent].node_id
                via_child_id: NodeID = self.nodes[current].node_id

                tables[ancestor_id].add_descendant(destination_id, via_child_id)
                current = parent
                parent  = predecessors[current]

        return tables

    def get_path(self, predecessors: "List[Optional[int]]", target_node: str, cost: float) -> Path:
        """
        @predecessors: A list of the predecessors node's indexes.

        @target_node:  The target node to reach from BASE.

        @cost:         The cost of the path.

        returns Path object
        """
        node_path: "List[NodeType]" = []
        current = self.nodes_index[target_node]

        while current is not None:
            node_path.insert(0, self.nodes[current])
            current = predecessors[current]
            if current == self.base_index:
                node_path.insert(0, self.base)
                break

        return Path(node_path, cost)

    def get_all_paths(self) -> "List[Path]":
        """
        Runs Graph.get_path() on all registered nodes.

        Returns a List[Path] for all nodes.
        """
        distances, predecessors = self.dijkstra()
        node_paths: "List[Path]" = []

        for i, cost in enumerate(distances):
            node_path = self.get_path(predecessors, self.nodes[i].name, cost)
            node_paths.append(node_path)

        return node_paths

if __name__ == "__main__":
    graph = Graph()

    graph.add_node("A", NodeID(1))
    graph.add_node("B", NodeID(2))
    graph.add_node("C", NodeID(3))
    graph.add_node("D", NodeID(4))
    graph.add_node("E", NodeID(5))

    graph.add_edge("BASE", "A", 2)
    graph.add_edge("BASE", "B", 1)

    graph.add_edge("B", "C", 2)
    graph.add_edge("B", "D", 2)
    graph.add_edge("D", "E", 1)

    graph.add_edge("D", "A", 4)
    graph.add_edge("D", "C", 3)
    graph.add_edge("A", "B", 2)
    graph.add_edge("E", "C", 2)

    from pprint import pprint
    pprint(graph.connections_matrix)

    pprint(graph.build_routing_table())

    paths = graph.get_all_paths()

    for path in paths:
        print(path)
