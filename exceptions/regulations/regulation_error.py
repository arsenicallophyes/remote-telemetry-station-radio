"""
Define base exception for regulatory compliance violations.
"""

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional

class RegulationError(Exception):
    """
    Base exception for all regulatory compliance violations.
    These errors indicate the attempted operation would result
    in violation of local, regional, or international radio regulations.
    """
    def __init__(self, message: str, code: "Optional[int]" = None) -> None:
        super().__init__(message)
        self.code = code
