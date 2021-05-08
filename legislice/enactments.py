"""Enactments, their text, and cross-references between them."""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Sequence, List, Optional, Tuple, Union

from anchorpoint import TextQuoteSelector, TextPositionSelector
from anchorpoint.utils.ranges import RangeSet
from anchorpoint.schemas import TextPositionSetFactory
from anchorpoint.textselectors import TextPositionSet
from anchorpoint.textsequences import TextSequence

from legislice import citations

RawSelector = Union[str, Dict[str, str]]
RawEnactment = Dict[str, Union[Any, str, List[RawSelector]]]


@dataclass
class CrossReference:
    """
    A legislative provision's citation to another provision.

    :param target_uri:
        the path to the target provision from the document root.

    :param target_url:
        the URL to fetch the target provision from an API.

    :param reference_text:
        The text in the citing provision that represents the cross-reference.
        Generally, this text identifies the target provision.

    :param target_node:
        an identifier for the target URI in the API.
    """

    target_uri: str
    target_url: str
    reference_text: str
    target_node: Optional[int] = None

    def __repr__(self):
        return f'CrossReference(target_uri="{self.target_uri}", reference_text="{self.reference_text}")'


@dataclass
class CitingProvisionLocation:
    """
    Memo indicating where an Enactment can be downloaded.

    :param node:
        location of the citing provision in a legislative code

    :param start_date:
        start date of the citing version of the provision

    :param heading:
        heading text for the citing provision
    """

    node: str
    start_date: date
    heading: str = ""

    def __repr__(self):
        return f"({self.node} {self.start_date})"

    def __gt__(self, other: CitingProvisionLocation):
        if self.start_date != other.start_date:
            return self.start_date > other.start_date
        return self.node > other.node


@dataclass
class InboundReference:
    """A memo that a TextVersion has a citation to a specified target provision."""

    content: str
    reference_text: str
    target_uri: str
    locations: List[CitingProvisionLocation]

    def __str__(self):
        result = f"InboundReference to {self.target_uri}, from {self.latest_location()}"
        if len(self.locations) > 1:
            result = f"{result} and {len(self.locations) - 1} other locations"
        return result

    def latest_location(self) -> CitingProvisionLocation:
        """Get most recent location where the citing text has been enacted."""
        return max(self.locations)


class TextVersion:
    """Version of legislative text, enacted at one or more times and locations."""

    def __init__(
        self, content: str, url: Optional[str] = None, id: Optional[int] = None,
    ):
        """Check that TextVersion has content."""
        if not content:
            raise ValueError("TextVersion should not be created with no content.")
        self.content = content
        self.url = url
        self.id = id


class BaseEnactment:
    """
    Base class for Enactments.

    Whether connected to subnodes by linking, or nesting.

    :param node:
        identifier for the site where the provision is codified

    :param heading:
        full heading of the provision

    :param content:
        full text content at this node, even if not all of it is cited

    :param start_date:
        date when the text was enacted at the cited location

    :param known_revision_date:
        whether the "start_date" field is known to be a date
        when the provision was revised in the code where it was publised.
        If False, then the Enactment refers to a time range when the text was
        codified, without asserting that the Enactment was not codified at
        earlier dates. This field is useful when working from incomplete
        legislative records.

    :param end_date:
        date when the text was removed from the cited location

    :param selection:
        identifier for the parts of the provision being cited

    :param anchors:
        a list of selectors representing the part of some other document
        (e.g. an Opinion) that references the Enactment. Unlike the selection
        field, it doesn't reference part of the Enactment itself. For use as
        a temporary place to store the anchors until they can be moved over
        to the citing document.

    :param name:
        a user-assigned label for the object
    """

    def __init__(
        self,
        node: str,
        heading: str,
        start_date: date,
        known_revision_date: bool = True,
        text_version: Optional[TextVersion] = None,
        content: Optional[str] = None,
        end_date: Optional[date] = None,
        anchors: Union[List[TextPositionSelector], List[TextQuoteSelector]] = None,
        citations: List[CrossReference] = None,
        name: str = "",
        *args,
        **kwargs,
    ):
        """Save parameters as private attributes."""
        self.node = node
        if text_version:
            self.text_version: Optional[TextVersion] = text_version
        elif content:
            self.text_version = TextVersion(content=content)
        else:
            self.text_version = None

        self._heading = heading
        self._start_date = start_date
        self.known_revision_date = known_revision_date
        self._end_date = end_date
        self.anchors = anchors or []
        self._cross_references = citations or []
        self.name = name

    @property
    def heading(self):
        """Get heading text for this version of the Enactment."""
        return self._heading

    @property
    def content(self) -> str:
        """Get text for this version of the Enactment."""
        if not self.text_version:
            return ""
        return self.text_version.content

    @property
    def start_date(self):
        """Get date when Enactment's text version came into effect."""
        return self._start_date

    @property
    def end_date(self):
        """Get date when Enactment's text version was no longer in effect."""
        return self._end_date

    @property
    def children(self):
        """Get children attribute."""
        return self._children

    @property
    def selection(self):
        """Get selection attribute."""
        return self._selection

    @property
    def text(self):
        """Get content text of Enactment."""
        return self.content

    def get_identifier_part(self, index: int) -> Optional[str]:
        """Get a part of the split node identifier, by number."""
        identifier_parts = self.node.split("/")
        if len(identifier_parts) < (index + 1):
            return None
        return identifier_parts[index]

    @property
    def sovereign(self):
        """Get "sovereign" part of node identifier."""
        return self.get_identifier_part(1)

    @property
    def jurisdiction(self):
        """Get "sovereign" part of node identifier."""
        return self.sovereign

    @property
    def code(self):
        """Get "code" part of node identifier."""
        return self.get_identifier_part(2)

    @property
    def title(self):
        """Get "title" part of node identifier."""
        return self.get_identifier_part(3)

    @property
    def section(self):
        """Get "section" part of node identifier."""
        return self.get_identifier_part(4)

    @property
    def level(self) -> str:
        """Get level of code for this Enactment, e.g. "statute" or "regulation"."""
        code_name, code_level_name = citations.identify_code(self.sovereign, self.code)
        return code_level_name

    @property
    def padded_length(self):
        """Get length of self's content plus one character for space before next section."""
        if self.content:
            return len(self.content) + 1
        return 0

    def __str__(self):
        text_sequence = self.text_sequence()
        return f'"{text_sequence}" ({self.node} {self.start_date})'

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(node="{self.node}", '
            f'start_date={repr(self.start_date)}, selection="{self.selection}")'
        )

    def as_citation(self) -> citations.Citation:
        """Create Citation Style Language markup for the Enactment."""
        level = self.level
        if level != "statute":
            raise NotImplementedError(
                f"Citation serialization not implemented for '{level}' provisions."
            )
        revision_date = self.start_date if self.known_revision_date else None
        return citations.Citation(
            jurisdiction=self.jurisdiction,
            code=self.code,
            volume=self.title,
            section=self.section,
            revision_date=revision_date,
        )

    def cross_references(self) -> List[CrossReference]:
        """Return all cross-references from this node and subnodes."""
        result = self._cross_references[:]
        for child in self.children:
            result += child.cross_references()
        return result

    def selected_text(self) -> str:
        """
        Return this provision's text that is within the ranges described by self.selection.

        Based on creating an :class:`anchorpoint.textsequences.TextSequence` from this Enactment's
        text content and the ranges in its selection attribute.
        """
        text_sequence = self.text_sequence()
        return str(text_sequence)

    def get_passage(
        self,
        selection: Union[
            bool,
            str,
            TextPositionSelector,
            TextQuoteSelector,
            Sequence[TextQuoteSelector],
        ],
    ) -> str:
        """Use text selector to get corresponding string from Enactment."""
        position_set = self.convert_selection_to_set(selection)
        return position_set.as_string(text=self.text)

    def convert_selection_to_set(
        self,
        selection: Union[
            bool,
            str,
            TextPositionSelector,
            TextPositionSet,
            TextQuoteSelector,
            Sequence[TextQuoteSelector],
        ],
    ) -> TextPositionSet:
        """Create a TextPositionSet from a different selection method."""
        if selection is True:
            return TextPositionSet(
                TextPositionSelector(0, len(self.content) + 1, include_end=False)
            )
        factory = TextPositionSetFactory(self.text)
        return factory.from_selection(selection)

    def convert_quotes_to_position(
        self, quotes: Sequence[TextQuoteSelector]
    ) -> TextPositionSet:
        """Convert quote selector to the corresponding position selector for this Enactment."""
        factory = TextPositionSetFactory(passage=self.text)
        return factory.from_quote_selectors(quotes)

    def select_from_text_positions_without_nesting(
        self, selections: Union[List[TextPositionSelector], RangeSet]
    ) -> TextPositionSet:
        r"""
        Move selectors from `selection` to `self._selection` and return any that can't be used.

        Replaces any preexisting _selection attribute on this Enactment object.

        :param selection:
            A TextPositionSet of TextPositionSelectors to apply to this Enactment.

        :returns:
            Any unused selections (beyond the end of the node content)
        """
        self._selection: List[TextPositionSelector] = []

        if isinstance(selections, RangeSet):
            selections = selections.ranges()
        selections = deque(selections)

        while selections and selections[0].start < len(self.content):
            current = selections.popleft()
            if current.end < len(self.content):
                self._selection.append(current)
            else:
                self._selection.append(
                    TextPositionSelector(start=current.start, end=len(self.content))
                )
                if current.end > self.padded_length:
                    selections.appendleft(
                        TextPositionSelector(start=self.padded_length, end=current.end)
                    )
        selection_as_set = TextPositionSet(self._selection)
        self._selection = selection_as_set.add_margin(text=self.content, margin_width=4)
        return TextPositionSet(selections)

    def select_without_children(
        self,
        selection: Union[
            bool,
            str,
            TextPositionSelector,
            TextPositionSet,
            TextQuoteSelector,
            Sequence[TextQuoteSelector],
        ],
    ) -> None:
        """Add new text selection, replacing any prior selection."""
        if not isinstance(selection, TextPositionSet):
            selection = self.convert_selection_to_set(selection)
        unused_selectors = self.select_from_text_positions_without_nesting(selection)
        self.raise_error_for_extra_selector(unused_selectors)

    def select(
        self,
        selection: Union[
            bool,
            TextPositionSelector,
            TextPositionSet,
            TextQuoteSelector,
            Sequence[TextQuoteSelector],
        ],
    ) -> None:
        """Add new text selection, replacing any prior selection."""
        self.select_without_children(selection)

    def text_sequence(self, include_nones: bool = True) -> TextSequence:
        """
        List the phrases in the Enactment selected by TextPositionSelectors.

        :param include_nones:
            Whether the list of phrases should include `None` to indicate a block of
            unselected text
        """
        return self.selection.as_text_sequence(
            text=self.content, include_nones=include_nones
        )

    def raise_error_for_extra_selector(
        self, unused_selectors: List[TextPositionSelector]
    ) -> None:
        """Raise an error if any passed selectors begin after the end of the text passage."""
        for selector in unused_selectors:
            if selector.start > len(self.content) + 1:
                raise ValueError(f'Selector "{selector}" was not used.')


class LinkedEnactment(BaseEnactment):
    """
    One or more passages of legislative text, selected from within a cited location.

    :param children:
        URLs of other nodes nested within this one
    """

    def __init__(
        self,
        children: List[str] = None,
        selection: Union[bool, List[TextPositionSelector]] = True,
        *args,
        **kwargs,
    ):
        """Select text of Enactment that can't have nested Enactments."""
        self._children = children or []
        super().__init__(*args, **kwargs)

        if selection:
            self.select_without_children(selection)
        else:
            self._selection = TextPositionSet()

    def select_all(
        self,
        selection: Union[
            bool,
            TextPositionSelector,
            TextPositionSet,
            TextQuoteSelector,
            Sequence[TextQuoteSelector],
        ] = True,
    ) -> None:
        """Select all text of enactment."""
        self.select_without_children(selection)


class Enactment(BaseEnactment):
    """
    One or more passages of legislative text, selected from within a cited location.

    :param children:
        other Enactments nested under this one's node

    :param selection:
        the parts of the Enactment that are being referenced
    """

    def __init__(
        self,
        children: List[Enactment] = None,
        selection: Union[bool, List[TextPositionSelector]] = True,
        *args,
        **kwargs,
    ):
        """Assign selected text as attr, including any selected text in child nodes."""
        self._children = children or []
        super().__init__(*args, **kwargs)
        self._selection = TextPositionSet()
        if selection:
            self.select_more(selection)

    @property
    def text(self):
        """Get all text including subnodes, regardless of which text is "selected"."""
        text_parts = [self.content]
        for child in self.children:
            if child.text:
                text_parts.append(child.text)
        joined = " ".join(text_parts)
        return joined.strip()

    def _tree_selection(
        self, selector_set: TextPositionSet, tree_length: int
    ) -> Tuple[TextPositionSet, int]:
        selectors_at_node = self.selection
        selectors_at_node_with_offset = selectors_at_node + tree_length
        new_tree_length = tree_length + self.padded_length
        new_selector_set = selector_set + selectors_at_node_with_offset

        for child in self.children:
            new_selector_set, new_tree_length = child._tree_selection(
                selector_set=new_selector_set, tree_length=new_tree_length
            )

        return new_selector_set, new_tree_length

    def tree_selection(self) -> TextPositionSet:
        """Return set of selectors for selected text in this provision and its children."""
        new_selector_set, new_tree_length = self._tree_selection(
            selector_set=TextPositionSet(), tree_length=0
        )
        return new_selector_set

    def select_more_text_at_current_node(
        self, added_selection: TextPositionSet
    ) -> None:
        """Select more text at this Enactment's node, not in child nodes."""
        new_selection = self.selection + added_selection
        self._selection = new_selection

    def select_more_text_in_current_branch(
        self, added_selection: TextPositionSet
    ) -> TextPositionSet:
        """Select more text within this Enactment's tree_selection, including child nodes."""
        new_selection = self.tree_selection() + added_selection
        return self.select_from_text_positions(new_selection)

    def _update_text_at_included_node(self, other: Enactment) -> Tuple[bool, bool]:
        """Recursively search child nodes for one that can be updated by `other`."""
        if self.node == other.node:
            found_node = True
            if self.text == other.text:
                self.select_more_text_in_current_branch(other.selection)
                updated_selection = True
            else:
                try:
                    self.select_more_text_from_changed_version(other)
                    updated_selection = True
                except ValueError:
                    updated_selection = False
            return found_node, updated_selection
        for child in self.children:
            if other.node.startswith(child.node):
                return child._update_text_at_included_node(other)
        return False, False

    def _add_enactment_at_included_node(self, other: Enactment) -> Enactment:
        """Add a selection of text at the same citation or at a child of self's citation."""
        if self >= other:
            return self

        copy_of_self = deepcopy(self)
        found_node, updated_selection = copy_of_self._update_text_at_included_node(
            other
        )
        if not found_node:
            raise ValueError(
                f"Unable to find node {other.node} (dated {other.start_date}) "
                f"among the descendants of node {self.node} (dated {self.start_date})."
            )
        if not updated_selection:
            raise ValueError(
                f'Unable to find the selected text "{other.selected_text()}" '
                f"(dated {other.start_date}) "
                f"at the citation {other.node} (dated {self.start_date})."
            )
        return copy_of_self

    def __add__(self, other: Enactment):

        if not isinstance(other, self.__class__):
            copy_of_self = deepcopy(self)
            copy_of_self.select_more(other)
            return copy_of_self

        if other.node.startswith(self.node):
            return self._add_enactment_at_included_node(other)
        elif self.node.startswith(other.node):
            return other._add_enactment_at_included_node(self)

        raise ValueError(
            "Can't add selected text from two different Enactments "
            "when neither is a descendant of the other."
        )

    def csl_json(self) -> str:
        """
        Serialize a citation to this provision in Citation Style Language JSON.

        Experimental feature.
        This CSL-JSON format currently only identifies the cited provision down to
        the section level. A citation to a subsection or deeper nested provision will
        be the same as a citation to its parent section.

        See https://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html for a
        guide to this CSL-JSON format.
        """
        citation = self.as_citation()
        return citation.as_json()

    def select_from_text_positions(self, selection: TextPositionSet) -> TextPositionSet:
        """Select text using position selectors and return any unused position selectors."""
        selections = self.select_from_text_positions_without_nesting(selection)

        selections = [selection - self.padded_length for selection in selections]
        for child in self.children:
            selections = child.select_from_text_positions(TextPositionSet(selections))
        return selections

    def select_all(self) -> None:
        """Select all text of Enactment."""
        if self.content:
            self._selection = TextPositionSet(
                TextPositionSelector(0, len(self.content))
            )
        else:
            self._selection = TextPositionSet()
        for child in self._children:
            child.select_all()

    def select_none(self) -> None:
        """Deselect any Enactment text, including in child nodes."""
        self._selection = TextPositionSet()
        for child in self._children:
            child.select_none()

    def select_more_text_from_changed_version(self, other: Enactment) -> None:
        """
        Select more text from a different text version at the same citation path.

        :param other:
            An :class:`Enactment` representing different text enacted at a
            different time, at the same `node` (or USLM path citation) as self.
            This Element's :attr:`~Enactment.node` attribute must be the same
            string as self's node attribute. It's not sufficient for `other`
            to have an Enactment listed in its :attr:`~Enactment._children`
            attribute with the same node attribute,
            or for `other` to have the same node attribute as an ancestor of self.
        """
        incoming_quote_selectors = [
            selector.as_quote_selector(other.text)
            for selector in other.tree_selection()
        ]
        incoming_position_selectors = []
        for quote_selector in incoming_quote_selectors:
            position = quote_selector.as_position(self.text)
            if position:
                incoming_position_selectors.append(position)
            if not quote_selector.is_unique_in(self.text):
                raise ValueError(
                    f"Incoming text selection {quote_selector} cannot be placed because it "
                    f"is not unique in the provision text."
                )
        self.select_more_text_in_current_branch(
            TextPositionSet(incoming_position_selectors)
        )

    def select_more(
        self,
        selection: Union[
            str,
            TextPositionSelector,
            TextPositionSet,
            TextQuoteSelector,
            Sequence[TextQuoteSelector],
        ],
    ) -> None:
        """Select text, in addition to any previous selection."""
        if not isinstance(selection, TextPositionSet):
            selection = self.convert_selection_to_set(selection)

        # Ignore child nodes if selector was passed in without an end
        if any(selector.end > 99999 for selector in selection):
            self.select_without_children(True)
        else:
            unused_selectors = self.select_more_text_in_current_branch(selection)
            self.raise_error_for_extra_selector(unused_selectors)

    def select(
        self,
        selection: Union[
            bool,
            str,
            TextPositionSelector,
            TextPositionSet,
            TextQuoteSelector,
            Sequence[TextQuoteSelector],
        ] = True,
        start: Optional[Union[int, str]] = None,
        end: Optional[Union[int, str]] = None,
    ) -> None:
        """
        Select text, clearing any previous selection.

        If the selection includes no selectors for child Enactments,
        then any selected passages for the child Enactments will be
        cleared.
        """
        if selection is False or selection is None:
            self.select_none()
        elif selection is True:
            self.select_all()
        else:
            if not isinstance(selection, TextPositionSet):
                selection = self.convert_selection_to_set(selection)
            unused_selectors = self.select_from_text_positions(selection)
            self.raise_error_for_extra_selector(unused_selectors)
        self.limit_selection(start=start, end=end)

    def limit_selection(
        self,
        start: Optional[Union[int, str]] = None,
        end: Optional[Union[int, str]] = None,
    ) -> None:
        """Limit selection to the range defined by start and end points."""
        if (start is not None) or (end is not None):
            selector = TextPositionSelector.from_text(
                text=self.text, start=start, end=end
            )
            new_selection = self.tree_selection() & selector
            self.select_from_text_positions(new_selection)

    def text_sequence(self, include_nones: bool = True) -> TextSequence:
        """
        List the phrases in the Enactment selected by TextPositionSelectors.

        :param include_nones:
            Whether the list of phrases should include `None` to indicate a block of
            unselected text
        """
        selected = super().text_sequence(include_nones=include_nones)
        for child in self.children:
            if selected:
                selected = selected + child.text_sequence(include_nones=include_nones)
            else:
                selected = child.text_sequence(include_nones=include_nones)

        return selected

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
            raise TypeError(
                f"Cannot compare {self.__class__.__name__} and {other.__class__.__name__} for same meaning."
            )
        self_selected_passages = self.text_sequence()
        other_selected_passages = other.text_sequence()
        return self_selected_passages.means(other_selected_passages)

    def implies(self, other: Enactment) -> bool:
        """Test whether ``self`` has all the text passages of ``other``."""
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Cannot compare {self.__class__.__name__} and {other.__class__.__name__} for implication."
            )
        self_selected_passages = self.text_sequence(include_nones=False)
        other_selected_passages = other.text_sequence(include_nones=False)
        return self_selected_passages >= other_selected_passages

    def __ge__(self, other: Enactment) -> bool:
        """
        Test whether ``self`` implies ``other``.

        :returns:
            Whether ``self`` contains at least all the same text as ``other``.
        """
        return self.implies(other)

    def __gt__(self, other) -> bool:
        """Test whether ``self`` implies ``other`` without having same meaning."""
        if self.means(other):
            return False
        return self.implies(other)


def consolidate_enactments(enactments: Sequence[Enactment]) -> List[Enactment]:
    r"""
    Consolidate any overlapping :class:`Enactment`\s in a :class:`list`.

    :param enactments:
        a list of :class:`Enactment`\s that may include overlapping
        legislative text within the same section

    :returns:
        a list of :class:`Enactment`\s without overlapping text
    """
    consolidated: List[Enactment] = []
    enactments = list(enactments)
    while enactments:
        match_made = False
        left = enactments.pop()
        for right in enactments:
            try:
                combined = left + right
                enactments.remove(right)
                enactments.append(combined)
                match_made = True
                break
            except ValueError:
                pass
        if not match_made:
            consolidated.append(left)
    return consolidated
