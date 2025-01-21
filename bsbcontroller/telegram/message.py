from dataclasses import dataclass
from typing import Optional, Type
from .types import Flag

from . import fields as f


@dataclass(frozen=True)
class Message:
    param: int
    flags: Flag
    fields: Optional[Type[f.Field]]
    name: str

    def __repr__(self) -> str:
        return f"Message({self.name})"
