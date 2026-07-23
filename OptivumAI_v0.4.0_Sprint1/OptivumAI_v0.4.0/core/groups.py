from __future__ import annotations

import re
from dataclasses import dataclass


_GROUP_PATTERN = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*$")


@dataclass(frozen=True, slots=True)
class GroupCode:
    """Znormalizowany kod grupy, np. 2/4."""

    number: int
    division_count: int

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("Numer grupy musi być większy od zera.")
        if self.division_count < 1:
            raise ValueError("Liczba grup musi być większa od zera.")
        if self.number > self.division_count:
            raise ValueError("Numer grupy nie może być większy od liczby grup.")

    @property
    def name(self) -> str:
        return f"{self.number}/{self.division_count}"


def parse_group_code(value: str | None) -> GroupCode | None:
    """Rozpoznaje zapis 1/2, 2/3, 4/4. Inne nazwy pozostają niestandardowe."""

    if not value:
        return None
    match = _GROUP_PATTERN.fullmatch(value)
    if not match:
        return None
    return GroupCode(number=int(match.group(1)), division_count=int(match.group(2)))
