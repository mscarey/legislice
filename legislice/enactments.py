from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Tuple, Union

from anchorpoint import TextQuoteSelector, TextPositionSelector


@dataclass(frozen=True)
class TextPassage:
    """
    A contiguous passage of legislative text.

    :param passage:
    """

    text: str

    def means(self, other: Optional[TextPassage]) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return self.text.strip(",:;. ") == other.text.strip(",:;. ")

    def __ge__(self, other: Optional[TextPassage]) -> bool:
        if not other:
            return True

        other_text = other.text.strip(",:;. ")
        return other_text in self.text


@dataclass(frozen=True)
class Enactment:
    """
    One or more passages of legislative text, selected from within a cited location.

    :param node:
        identifier for the site where the provision is codified

    :param heading:
        full heading of the provision

    :param content:
        full text content at this node, even if not all of it is cited

    :param children:
        other nodes nested within this one

    :param start_date:
        date when the text was enacted at the cited location

    :param end_date:
        date when the text was removed from the cited location

    :param selector:
        identifier for the part of the provision being cited
    """

    node: str
    heading: str
    content: str
    start_date: date
    end_date: Optional[date] = None
    children: List[Enactment] = field(default_factory=list)
    selection: Union[bool, Tuple[TextPositionSelector, ...]] = True

    def selected_as_list(
        self, include_nones: bool = True
    ) -> List[Union[None, TextPassage]]:
        selected: List[Union[None, TextPassage]] = []
        if self.selection is True:
            selected.append(TextPassage(self.content))
        elif include_nones and (not selected or selected[-1] is not None):
            selected.append(None)
        for child in self.children:
            selected += child.selected_as_list()
        return selected

    def selected_text(self) -> str:
        result = ""
        for phrase in self.selected_as_list():
            if phrase is None:
                if not result.endswith("..."):
                    result += "..."
            else:
                if result and not result.endswith(("...", " ")):
                    result += " "
                result += phrase.text
        return result

    def means(self, other: Enactment) -> bool:
        r"""
        Find whether meaning of ``self`` is equivalent to that of ``other``.

        ``Self`` must be neither broader nor narrower than ``other`` to return True.

        :returns:
            whether ``self`` and ``other`` represent the same text
            issued by the same sovereign in the same level of
            :class:`Enactment`\.
        """
        if not isinstance(other, self.__class__):
            return False
        self_selected_passages = self.selected_as_list()
        other_selected_passages = other.selected_as_list()
        zipped = zip(self_selected_passages, other_selected_passages)
        if not all((pair[0] is None) == (pair[1] is None) for pair in zipped):
            return False
        return all(pair[0] is None or pair[0].means(pair[1]) for pair in zipped)

    def __ge__(self, other):
        """
        Tells whether ``self`` implies ``other``.

        :returns:
            Whether ``self`` contains at least all the same text as ``other``.
        """
        if not isinstance(other, self.__class__):
            return False
        self_selected_passages = self.selected_as_list(include_nones=False)
        other_selected_passages = other.selected_as_list(include_nones=False)
        for other_passage in other_selected_passages:
            if not any(
                self_passage >= other_passage for self_passage in self_selected_passages
            ):
                return False
        return True

    def __gt__(self, other) -> bool:
        """Test whether ``self`` implies ``other`` without having same meaning."""
        if self == other:
            return False
        return self >= other
