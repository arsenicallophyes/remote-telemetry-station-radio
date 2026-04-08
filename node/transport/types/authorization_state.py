try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import NewType
    AuthorizationStateType = NewType("AuthorizationStateType", int)
else:
    AuthorizationStateType = int

class AuthorizationState:
    """
    @enum
    """
    PENDING      = AuthorizationStateType(0)
    REGISTERED   = AuthorizationStateType(1)
