"""EnactmentGroup class."""

from __future__ import annotations

import textwrap
from typing import List, Sequence, Union

from legislice.enactments import Enactment, EnactmentPassage, consolidate_enactments
from pydantic import BaseModel, validator


def sort_passages(passages: List[EnactmentPassage]) -> List[EnactmentPassage]:
    """
    Sort EnactmentPassages in group, in place.

    Sorts federal before state; constitutional before statute before regulation;
    and then alphabetically
    """
    passages.sort(key=lambda x: x.node)
    passages.sort(key=lambda x: x.level)
    passages.sort(key=lambda x: x.is_federal, reverse=True)
    return passages


class EnactmentGroup(BaseModel):
    """Group of Enactments with comparison methods."""

    passages: List[EnactmentPassage] = []

    @validator("passages", pre=True)
    def consolidate_passages(
        cls,
        obj: Union[
            EnactmentGroup,
            Enactment,
            EnactmentPassage,
            List[Union[Enactment, EnactmentPassage]],
        ],
    ) -> List[EnactmentPassage]:
        """Consolidate overlapping EnactmentPassages into fewer objects."""
        if isinstance(obj, EnactmentGroup):
            return obj.passages
        if not isinstance(obj, List):
            obj = [obj]
        consolidated: List[EnactmentPassage] = consolidate_enactments(obj)
        return consolidated

    @validator("passages")
    def sort_passages(cls, obj: List[EnactmentPassage]) -> List[EnactmentPassage]:
        """Sort federal to state, constitutional to statute to regulation, and then alphabetically."""

        return sort_passages(obj)

    def _at_index(self, key: int) -> EnactmentPassage:
        return self.passages[key]

    def __getitem__(
        self, key: Union[int, slice]
    ) -> Union[EnactmentPassage, EnactmentGroup]:
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            return self.__class__(
                passages=[self._at_index(i) for i in range(start, stop, step)]
            )
        return self._at_index(key)

    def __iter__(self):
        yield from self.passages

    def __len__(self):
        return len(self.passages)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(list(self.passages))})"

    def __str__(self):
        result = "the group of Enactments:"
        indent = "  "
        for factor in self.passages:
            result += f"\n{textwrap.indent(str(factor), prefix=indent)}"
        return result

    def _add_group(self, other: EnactmentGroup) -> EnactmentGroup:
        combined = self.passages[:] + other.passages[:]
        return self.__class__(passages=combined)

    def __add__(
        self, other: Union[EnactmentGroup, Sequence[Enactment], Enactment]
    ) -> EnactmentGroup:
        """Combine two EnactmentGroups, consolidating any duplicate Enactments."""
        if isinstance(other, self.__class__):
            return self._add_group(other)
        to_add = self.__class__(passages=other)
        return self._add_group(to_add)

    def __ge__(self, other: Union[Enactment, EnactmentPassage, EnactmentGroup]) -> bool:
        """Test whether ``self`` implies ``other`` and ``self`` != ``other``."""
        return bool(self.implies(other))

    def __gt__(self, other: Union[Enactment, EnactmentPassage, EnactmentGroup]) -> bool:
        """Test whether ``self`` implies ``other`` and ``self`` != ``other``."""
        return bool(self.implies(other))

    def _implies_enactment(self, other: Union[Enactment, EnactmentPassage]) -> bool:
        return any(self_enactment.implies(other) for self_enactment in self)

    def _implies(self, other: EnactmentGroup) -> bool:
        return all(self._implies_enactment(other_law) for other_law in other)

    def implies(
        self, other: Union[Enactment, EnactmentPassage, EnactmentGroup]
    ) -> bool:
        """Determine whether self includes all the text of another Enactment or EnactmentGroup."""
        if isinstance(other, (Enactment, EnactmentPassage)):
            return self._implies_enactment(other)
        return self._implies(other)
