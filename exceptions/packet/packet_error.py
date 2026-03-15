try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional

class PacketError(Exception):
    """
    Base exception for all packet requirments violations.
    """
    def __init__(self, message: str, code: "Optional[int]" = None) -> None:
        super().__init__(message)
        self.code = code
