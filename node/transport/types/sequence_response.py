try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import NewType
    SequenceResponseType = NewType("SequenceResponseType", int)
else:
    SequenceResponseType = int

class SequenceResponse:
    """
    @enum
    """
    SUCCESS      = SequenceResponseType(0)
    AHEAD        = SequenceResponseType(1)
    DUPLICATE    = SequenceResponseType(2)
    UNREGISTERED = SequenceResponseType(3)
    PENDING      = SequenceResponseType(4)
    ABORT        = SequenceResponseType(5)
