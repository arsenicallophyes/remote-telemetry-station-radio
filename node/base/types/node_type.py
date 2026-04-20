from models.model import NodeID
class NodeType:
    """
    @dataclass
    """

    __slots__ = (
        "name",
        "node_id",
    )

    def __init__(self, name: str, node_id : NodeID) -> None:
        self.name = name
        self.node_id = node_id

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, value: object) -> bool:
        return value == self.name

    def __str__(self) -> str:
        return self.name
