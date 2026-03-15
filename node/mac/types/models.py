try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import NewType
    UsedTime = NewType("UsedTime", float)
    WaitTime = NewType("WaitTime", float)
else:
    UsedTime = float
    WaitTime = float
