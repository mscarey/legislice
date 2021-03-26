"""EnactmentGroup class."""

from __future__ import annotations

import textwrap
from typing import List, Optional, Sequence, Tuple, Union

from legislice.enactments import Enactment, consolidate_enactments


class EnactmentGroup:
    """Group of Enactments with comparison methods."""

    def __init__(
        self,
        enactments: Optional[
            Union[EnactmentGroup, Sequence[Enactment], Enactment]
        ] = None,
    ):
        """Normalize ``factors`` as sequence attribute."""
        if isinstance(enactments, EnactmentGroup):
            self.sequence: List[Enactment] = enactments.sequence
        elif isinstance(enactments, Sequence):
            self.sequence = list(enactments)
        elif enactments is None:
            self.sequence = []
        else:
            self.sequence = [enactments]
        for enactment in self.sequence:
            if not isinstance(enactment, Enactment):
                raise TypeError(
                    f'Object "{enactment} could not be included in '
                    f"{self.__class__.__name__} because it is "
                    f"type {enactment.__class__.__name__}, not type Enactment"
                )
        self.sequence = consolidate_enactments(self.sequence)
        self.sequence.sort(key=lambda x: x.node)

    def _at_index(self, key: int) -> Enactment:
        return self.sequence[key]

    def __getitem__(self, key: Union[int, slice]) -> Enactment:
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            return self.__class__([self._at_index(i) for i in range(start, stop, step)])
        return self._at_index(key)

    def __iter__(self):
        yield from self.sequence

    def __len__(self):
        return len(self.sequence)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(list(self.sequence))})"

    def __str__(self):
        result = "the group of Enactments:"
        indent = "  "
        for factor in self.sequence:
            result += f"\n{textwrap.indent(str(factor), prefix=indent)}"
        return result

    def _add_group(self, other: EnactmentGroup) -> EnactmentGroup:
        combined = self.sequence[:] + other.sequence[:]
        return self.__class__(combined)

    def __add__(
        self, other: Union[EnactmentGroup, Sequence[Enactment], Enactment]
    ) -> EnactmentGroup:
        """Combine two EnactmentGroups, consolidating any duplicate Enactments."""
        if isinstance(other, self.__class__):
            return self._add_group(other)
        to_add = self.__class__(other)
        return self._add_group(to_add)

    def __ge__(self, other: Union[Enactment, EnactmentGroup]) -> bool:
        """Test whether ``self`` implies ``other`` and ``self`` != ``other``."""
        return bool(self.implies(other))

    def __gt__(self, other: Union[Enactment, EnactmentGroup]) -> bool:
        """Test whether ``self`` implies ``other`` and ``self`` != ``other``."""
        return bool(self.implies(other))

    def _implies_enactment(self, other: Enactment) -> bool:
        return any(self_enactment.implies(other) for self_enactment in self)

    def _implies(self, other: EnactmentGroup) -> bool:
        return all(self._implies_enactment(other_law) for other_law in other)

    def implies(self, other: Union[Enactment, EnactmentGroup]) -> bool:
        """Determine whether self includes all the text of another Enactment or EnactmentGroup."""
        if isinstance(other, Enactment):
            return self._implies_enactment(other)
        return self._implies(other)
