try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False  # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional
    from node.transport.types.recovery_state import RecoveryState
    from node.transport.types.retransmit_state import RetransmitState


class NodeState:
    recovery:       "Optional[RecoveryState]"
    retransmit:     "Optional[RetransmitState]"
