from regulations.duty_cycles import DutyCyclesType

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional



class Band:

    __slots__ = ("name", "start", "end", "erp", "duty_cycle", "note")

    def __init__(
            self,
            name: str,
            start: float,
            end: float,
            erp: int,
            duty_cycle: "DutyCyclesType",
            note: "Optional[str]",
        ) -> None:
        self.name = name
        self.start = start
        self.end = end
        self.erp = erp
        self.duty_cycle = duty_cycle
        self.note = note
