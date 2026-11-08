from dataclasses import dataclass

@dataclass(frozen=True)
class Token:
    kind: str
    value: object
    line: int
    column: int
