from models.model import NodeID

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from time import struct_time
    from typing import Optional, Tuple


MAX_SEQ = 256 # 0 - 255
HALF = MAX_SEQ // 2 # 128
class Peer:
    """
    @dataclass
    """
    __slots__ = (
        "node_id",
        "transmit",
        "receive",
    )

    def __init__(self, node_id: "NodeID") -> None:
        self.node_id = node_id
        self.transmit = TransmitState()
        self.receive = ReceiveState()


class ReceiveState:

    __slots__ = (
        "last_seen",
        "last_received_timestamp",
        "last_seq",
        "expected_seq",
        "missed_packets",
        "link_quality",
    )

    def __init__(self) -> None:
        self.last_seen               : "Optional[struct_time]" = None
        self.last_received_timestamp : int = 0
        self.last_seq                : int = 0
        self.expected_seq            : int = 0
        self.link_quality            : float = 0
        self.missed_packets          : "Optional[Tuple[int,...]]" = None

    def increment_sequence(self) -> None:
        self.expected_seq = (self.expected_seq + 1) % MAX_SEQ

    def set_sequence(self, seq: int) -> None:
        if 0 <= seq < MAX_SEQ:
            self.expected_seq = seq

    def seq_delta(self, seq: int, expected: int) -> int:
        return (seq - expected) % MAX_SEQ
    
    def complete_recovery(self, ahead_seq: int):
        self.set_sequence(ahead_seq)
        self.increment_sequence()

class TransmitState:

    __slots__ = (
        "next_seq",
    )

    def __init__(self) -> None:
        self.next_seq = 0

    def increment_sequence(self) -> None:
        self.next_seq = (self.next_seq + 1) % MAX_SEQ
