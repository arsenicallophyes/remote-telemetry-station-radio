from typing import Optional
from dataclasses import dataclass
from Codebase.regulations.duty_cycles import DutyCycles


@dataclass(frozen=True, slots=True)
class Band():
    name: str
    start: float
    end: float
    erp: int
    duty_cycle: DutyCycles
    note: Optional[str]
