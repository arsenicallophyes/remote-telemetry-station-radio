try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Literal, TypeAlias, NewType
    SpreadingFactor: TypeAlias = Literal[6, 7, 8, 9, 10, 11, 12]
    CodingRate: TypeAlias = Literal[5, 6, 7, 8]
    Frequency = NewType("Frequency", float)
    NodeID = NewType("NodeID", int)
else:
    SpreadingFactor = int
    CodingRate = int
    Frequency = float
    NodeID = int
