from models.model import NodeID
from models.packet import Packet


try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Set

class RetransmitState:
    """
    @dataclass
    """

    __slots__ = (
        "target",
        "queued_packets"
    )

    def __init__(self, target: NodeID, queued_packets: "Set[Packet]") -> None:
        self.target           = target
        self.queued_packets   = queued_packets
