
from regulations.band import Band

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import TypeAlias, Sequence
    BandsSeq: TypeAlias = Sequence[Band]
else:
    BandsSeq = "Sequence[Band]"
