from models.model import NodeID

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False  # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional, Dict

PATH_UPDATE_NONE = 0xFF

class RoutingTable:
    def __init__(self, node_id: NodeID, base_id: NodeID) -> None:
        self.node_id = node_id
        self.base_id = base_id

        self.parent        : "Optional[NodeID]"     = None
        self.backup_parent : "Optional[NodeID]"     = None
        self.children      : "Dict[NodeID, NodeID]" = {}

    def set_parents(self, parent: "Optional[NodeID]", backup: "Optional[NodeID]") -> None:
        self.parent        = parent
        self.backup_parent = backup

    def add_descendant(self, destination: NodeID, via_child: NodeID) -> None:
        self.children[destination] = via_child

    def clear(self) -> None:
        self.parent        = None
        self.backup_parent = None
        self.children      = {}

    def next_hop(self, destination: NodeID, use_backup: bool = False) -> "Optional[NodeID]":
        if destination == self.node_id:
            return self.node_id

        if destination == self.base_id:
            if use_backup:
                return self.backup_parent
            return self.parent

        if destination in self.children:
            return self.children[destination]

        return None

    def serialize(self) -> bytes:
        """
        byte 0     : parent NodeID        (0xFF = None)
        byte 1     : backup_parent NodeID (0xFF = None)
        byte 2     : n = number of descendant entries
        bytes 3+   : n pairs of (destination NodeID, via_child NodeID)
        """
        parent_byte = PATH_UPDATE_NONE if self.parent is None else int(self.parent)
        backup_byte = PATH_UPDATE_NONE if self.backup_parent is None else int(self.backup_parent)

        n = len(self.children)
        buf = bytearray()
        buf.append(parent_byte)
        buf.append(backup_byte)
        buf.append(n)

        for destination, via_child in self.children.items():
            buf.append(int(destination))
            buf.append(int(via_child))

        return buf

    @classmethod
    def deserialize(cls, node_id: NodeID, base_id: NodeID, data: bytes) -> "RoutingTable":
        if len(data) < 3:
            raise ValueError("Path update too short")

        table = cls(node_id, base_id)
        parent_byte = data[0]
        backup_byte = data[1]
        n           = data[2]

        if parent_byte != PATH_UPDATE_NONE:
            table.parent = NodeID(parent_byte)

        if backup_byte != PATH_UPDATE_NONE:
            table.backup_parent = NodeID(backup_byte)

        expected_len = 3 + n * 2

        if len(data) < expected_len:
            raise ValueError("Incomplete Data")

        for i in range(n):
            offset = 3 + i * 2
            dest_byte = data[offset]
            via_byte  = data[offset + 1]
            table.children[NodeID(dest_byte)] = NodeID(via_byte)

        return table

    def __repr__(self) -> str:
        return (
            f"RoutingTable("
            f"self={self.node_id}, "
            f"parent={self.parent}, "
            f"backup={self.backup_parent}, "
            f"children={self.children})"
        )
