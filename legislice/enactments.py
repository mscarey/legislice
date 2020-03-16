from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Tuple, Union

from anchorpoint import TextQuoteSelector, TextPositionSelector


@dataclass(frozen=True)
class Enactment:
    """
    A passage of legislative text.

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

    def selected_as_list(self) -> List[Union[None, str]]:
        selected: List[Union[None, str]] = []
        if self.selection is True:
            selected.append(self.content)
        elif self.selection is False:
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
                result += phrase
        return result
