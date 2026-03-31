from models.model import NodeID

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Set


class RecoveryState:
    """
    @dataclass
    """

    __slots__ =(
        "source",
        "queued_packets",
        "ahead_seq"
    )

    def __init__(
            self,
            source: NodeID,
            queued_packets: "Set[int]",
            ahead_seq: int,
        ) -> None:
        self.source             = source
        self.queued_packets     = queued_packets
        self.ahead_seq          = ahead_seq
