"""Enactments, their text, and cross-references between them."""

from __future__ import annotations

from copy import deepcopy

from datetime import date
from typing import Sequence, List, Optional, Tuple, Union

from anchorpoint import TextQuoteSelector, TextPositionSelector
from anchorpoint.textselectors import TextPositionSet, TextSelectionError
from anchorpoint.textselectors import TextPositionSetFactory
from anchorpoint.textsequences import TextSequence

from legislice.citations import Citation, identify_code, CodeLevel
from legislice.types import InboundReferenceDict

from pydantic import BaseModel, validator, root_validator
from ranges import Range, RangeDict


class CrossReference(BaseModel):
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

    def __str__(self):
        return f'CrossReference(target_uri="{self.target_uri}", reference_text="{self.reference_text}")'


class CitingProvisionLocation(BaseModel):
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

    def __str__(self):
        return f"({self.node} {self.start_date})"

    def __lt__(self, other: CitingProvisionLocation):
        if self.start_date != other.start_date:
            return self.start_date < other.start_date
        return self.node < other.node


class InboundReference(BaseModel):
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

    @root_validator(pre=True)
    def search_citations_for_reference_text(
        cls, values: InboundReferenceDict
    ) -> InboundReferenceDict:
        """Get reference_text field from nested "citations" model."""
        if not values.get("reference_text"):
            reference_text = ""
            for citation in values["citations"]:
                if citation["target_uri"] == values["target_uri"]:
                    reference_text = citation["reference_text"]
            values["reference_text"] = reference_text

        return values


class TextVersion(BaseModel):
    """Version of legislative text, enacted at one or more times and locations."""

    content: str
    url: Optional[str] = None
    id: Optional[int] = None

    @validator("content")
    def content_exists(cls, content: str) -> str:
        """Check that the text content is a non-empty string."""

        if not content:
            raise ValueError(
                "TextVersion should not be created with an empty string for content."
            )
        return content


class EnactmentMemo(BaseModel):
    """
    Info about an Enactment, to be linked to its text position in a parent Enactment.

    Used when recursively searching the parent Enactment.
    """

    node: str
    start_date: date
    content: str
    end_date: Optional[date] = None


class Enactment(BaseModel):
    """
    Base class for Enactments.

    Whether connected to subnodes by linking, or nesting.

    :param node:
        identifier for the site where the provision is codified

    :param heading:
        full heading of the provision

    :param text_version:
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

    :param first_published:
        date when this Enactment's code was first published.

    :param earliest_in_db:
        date of the earliest version of this Enactment in the database.
        Used to determine whether the start_date of the Enactment is
        a date when the Enactment was amended or first published.

    :param anchors:
        a list of selectors representing the part of some other document
        (e.g. an Opinion) that references the Enactment. Unlike the selection
        field, it doesn't reference part of the Enactment itself. For use as
        a temporary place to store the anchors until they can be moved over
        to the citing document.

    :param name:
        a user-assigned label for the object
    """

    node: str
    start_date: date
    heading: str = ""
    text_version: Optional[TextVersion] = None
    end_date: Optional[date] = None
    first_published: Optional[date] = None
    earliest_in_db: Optional[date] = None
    anchors: Union[
        TextPositionSet, List[Union[TextPositionSelector, TextQuoteSelector]]
    ] = []
    citations: List[CrossReference] = []
    name: str = ""
    children: Union[List[Enactment], List[str]] = []

    @validator("text_version", pre=True)
    def make_text_version_from_str(
        cls, value: Optional[Union[TextVersion, str]]
    ) -> Optional[TextVersion]:
        """Allow content to be used to populate text_version."""
        if isinstance(value, str):
            if value:
                return TextVersion(content=value)
            return None
        return value or None

    @property
    def content(self) -> str:
        """Get text for this version of the Enactment."""
        if not self.text_version:
            return ""
        return self.text_version.content

    @property
    def nested_children(self):
        """Get nested children attribute."""
        return [child for child in self.children if isinstance(child, Enactment)]

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
    def is_federal(self):
        """Check if self is from a federal jurisdiction."""
        return self.sovereign == "us"

    @property
    def level(self) -> CodeLevel:
        """Get level of code for this Enactment, e.g. "statute" or "regulation"."""
        code_name, code_level_name = identify_code(self.sovereign, self.code)
        return code_level_name

    @property
    def padded_length(self):
        """Get length of self's content plus one character for space before next section."""
        if self.content:
            return len(self.content) + 1
        return 0

    @property
    def known_revision_date(self) -> bool:
        r"""
        Determine if Enactment's start_date reflects its last revision date.

        If not, then the `start_date` merely reflects the earliest date that versions
        of the :class:`Enactment`\'s code exist in the database.
        """
        if self.earliest_in_db:
            if self.earliest_in_db < self.start_date:
                return True
            elif self.first_published and self.earliest_in_db <= self.first_published:
                return True
        return False

    def __str__(self):
        return f"{self.node} ({self.start_date})"

    def as_citation(self) -> Citation:
        """Create Citation Style Language markup for the Enactment."""
        level = self.level
        if level != CodeLevel.STATUTE:
            raise NotImplementedError(
                f"Citation serialization not implemented for '{level}' provisions."
            )
        revision_date = self.start_date if self.known_revision_date else None
        return Citation(
            jurisdiction=self.jurisdiction,
            code=self.code,
            volume=self.title,
            section=self.section,
            revision_date=revision_date,
        )

    def cross_references(self) -> List[CrossReference]:
        """Return all cross-references from this node and subnodes."""
        result = self.citations[:]
        for child in self.nested_children:
            result += child.cross_references()
        return result

    def get_string(
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
            return self.make_selection_of_all_text()
        factory = TextPositionSetFactory(self.text)
        return factory.from_selection(selection)

    def convert_quotes_to_position(
        self, quotes: Sequence[TextQuoteSelector]
    ) -> TextPositionSet:
        """Convert quote selector to the corresponding position selector for this Enactment."""
        factory = TextPositionSetFactory(text=self.text)
        return factory.from_quote_selectors(quotes)

    def limit_selection(
        self,
        selection: TextPositionSet,
        start: int = 0,
        end: Optional[int] = None,
    ) -> TextPositionSet:
        """Limit selection to the range defined by start and end points."""

        limit_selector = TextPositionSelector.from_text(
            text=self.text, start=start, end=end
        )
        return selection & limit_selector

    def limit_selection_to_current_node(
        self, selection: TextPositionSet
    ) -> TextPositionSet:
        """Limit selection to the current node."""
        return self.limit_selection(selection=selection, start=0, end=len(self.text))

    def text_sequence(self, include_nones=True) -> TextSequence:
        """Get a sequence of text passages for this provision and its subnodes."""
        selection = self.tree_selection()
        return selection.as_text_sequence(text=self.text, include_nones=include_nones)

    def means(self, other: Union[Enactment, EnactmentPassage]) -> bool:
        """Determine if self and other have identical text."""
        if not isinstance(other, (EnactmentPassage, Enactment)):
            raise TypeError(
                f"Cannot compare {self.__class__.__name__} and {other.__class__.__name__} for same meaning."
            )
        self_selected_passages = self.text_sequence()
        other_selected_passages = other.text_sequence()
        return self_selected_passages.means(other_selected_passages)

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
        start: int = 0,
        end: Optional[int] = None,
    ) -> EnactmentPassage:
        """Select text from Enactment."""
        selection_set = self.make_selection(selection=selection, start=start, end=end)
        return EnactmentPassage(enactment=self, selection=selection_set)

    def select_all(self) -> EnactmentPassage:
        """Return a passage for this Enactment, including all subnodes."""
        selection = self.make_selection_of_all_text()
        return EnactmentPassage(enactment=self, selection=selection)

    def make_selection_of_all_text(self) -> TextPositionSet:
        """Return a TextPositionSet of all text in this Enactment."""
        if self.text:
            return TextPositionSet(
                positions=TextPositionSelector(start=0, end=len(self.text))
            )
        return TextPositionSet()

    def make_selection(
        self,
        selection: Union[
            bool,
            str,
            TextPositionSelector,
            TextPositionSet,
            TextQuoteSelector,
            Sequence[TextQuoteSelector],
        ] = True,
        start: int = 0,
        end: Optional[int] = None,
    ) -> TextPositionSet:
        """Make a TextPositionSet for specified text in this Enactment."""
        if selection is False or selection is None:
            return TextPositionSet()
        elif not isinstance(selection, TextPositionSet):
            selection = self.convert_selection_to_set(selection)

        limited = self.limit_selection(selection=selection, start=start, end=end)
        self.raise_error_for_extra_selector(limited)
        return limited

    def raise_error_for_extra_selector(self, selection: TextPositionSet) -> None:
        """Raise an error if any passed selectors begin after the end of the text passage."""
        for selector in selection.positions:
            if selector.start > len(self.text) + 1:
                raise ValueError(f'Selector "{selector}" was not used.')

    def make_selection_of_this_node(self) -> TextPositionSet:
        """Return a TextPositionSet of the text at this node, not child nodes."""
        if not self.content:
            return TextPositionSet()
        return TextPositionSet(
            positions=TextPositionSelector(start=0, end=len(self.content))
        )

    def _rangedict(
        self, range_dict: RangeDict, tree_length: int
    ) -> Tuple[RangeDict, int]:
        if self.content:
            span = Range(start=tree_length, end=tree_length + len(self.content))
            range_dict[span] = EnactmentMemo(
                node=self.node,
                start_date=self.start_date,
                content=self.content,
                end_date=self.end_date,
            )
        new_tree_length = tree_length + self.padded_length

        for child in self.nested_children:
            range_dict, new_tree_length = child._rangedict(
                range_dict=range_dict, tree_length=new_tree_length
            )

        return range_dict, new_tree_length

    def rangedict(self) -> RangeDict:
        """Return a RangeDict matching text spans to Enactment attributes."""
        new_range_dict, new_tree_length = self._rangedict(
            range_dict=RangeDict(), tree_length=0
        )
        return new_range_dict

    @property
    def span_length(self) -> int:
        """Return the length of the span of this Enactment."""
        return self.padded_length + sum(
            child.span_length for child in self.nested_children
        )

    def _tree_selection(
        self, selector_set: TextPositionSet, tree_length: int
    ) -> Tuple[TextPositionSet, int]:
        selectors_at_node = self.make_selection_of_this_node()
        selectors_at_node_with_offset = selectors_at_node + tree_length
        new_tree_length = tree_length + self.padded_length
        new_selector_set = selector_set + selectors_at_node_with_offset

        for child in self.nested_children:
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
        return citation.csl_json()

    @property
    def text(self):
        """Get all text including subnodes, regardless of which text is "selected"."""
        text_parts = [self.content]

        for child in self.nested_children:
            if child.text:
                text_parts.append(child.text)
        joined = " ".join(text_parts)
        return joined.strip()

    def implies(self, other: Union[Enactment, EnactmentPassage]) -> bool:
        """Test whether ``self`` has all the text passages of ``other``."""
        if not isinstance(other, (Enactment, EnactmentPassage)):
            raise TypeError(
                f"Cannot compare {self.__class__.__name__} and {other.__class__.__name__} for implication."
            )
        self_selected_passages = self.text_sequence(include_nones=False)
        other_selected_passages = other.text_sequence(include_nones=False)
        return self_selected_passages >= other_selected_passages

    def __ge__(self, other: Union[Enactment, EnactmentPassage]) -> bool:
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


Enactment.update_forward_refs()


class EnactmentPassage(BaseModel):
    """An Enactment with selectors indicating which text is being referenced."""

    enactment: Enactment
    selection: TextPositionSet = TextPositionSet(
        positions=TextPositionSelector(start=0, end=None)
    )

    @property
    def text(self):
        """Get all text including subnodes, regardless of which text is "selected"."""
        return self.enactment.text

    @property
    def sovereign(self):
        """Get "sovereign" part of node identifier."""
        return self.enactment.sovereign

    @property
    def jurisdiction(self):
        """Get "sovereign" part of node identifier."""
        return self.enactment.sovereign

    @property
    def code(self):
        """Get "code" part of node identifier."""
        return self.enactment.code

    @property
    def title(self):
        """Get "title" part of node identifier."""
        return self.enactment.title

    @property
    def section(self):
        """Get "section" part of node identifier."""
        return self.enactment.section

    @property
    def is_federal(self):
        """Check if self is from a federal jurisdiction."""
        return self.enactment.is_federal

    @property
    def level(self) -> CodeLevel:
        """Get level of code for this Enactment, e.g. "statute" or "regulation"."""
        return self.enactment.level

    @property
    def child_passages(self) -> List[EnactmentPassage]:
        """Return a list of EnactmentPassages for this Enactment's children."""
        result: List[EnactmentPassage] = []
        tree_length = self.enactment.padded_length
        for child in self.enactment.nested_children:
            selection = self.selection & TextPositionSelector(
                start=tree_length, end=tree_length + child.span_length
            )
            result.append(
                EnactmentPassage(enactment=child, selection=selection - tree_length)
            )
            tree_length += child.span_length
        return result

    @property
    def start_date(self):
        """Get the latest start date of any provision version included in the passage."""
        current = self.enactment.start_date
        ranges = self.enactment.rangedict()
        for span, memo in ranges.items():
            if self.selection.rangeset() & span[0]:
                if memo.start_date > current:
                    current = memo.start_date
        return current

    @property
    def end_date(self):
        """Get the earliest end date of any provision version included in the passage."""
        current = self.enactment.end_date
        ranges = self.enactment.rangedict()
        for span, memo in ranges.items():
            if self.selection.rangeset() & span[0]:
                if not current:
                    current = memo.end_date
                elif memo.end_date and memo.end_date < current:
                    current = memo.end_date
        return current

    @property
    def node(self):
        """Get the node that this Enactment is from."""
        return self.enactment.node

    def as_quotes(self) -> List[TextQuoteSelector]:
        """Return quote selectors for the selected text."""
        return [
            phrase.as_quote(self.enactment.text) for phrase in self.selection.positions
        ]

    def __str__(self):
        text_sequence = self.text_sequence()
        return f'"{text_sequence}" ({self.enactment.node} {self.start_date})'

    def select_all(self) -> None:
        """Select all text of Enactment."""
        text = self.enactment.text
        self.selection = TextPositionSet(
            positions=[TextPositionSelector(start=0, end=len(text))]
        )
        return None

    def limit_selection(
        self,
        start: int = 0,
        end: Optional[int] = None,
    ) -> None:
        """Limit selection to the range defined by start and end points."""

        limit_selector = TextPositionSelector.from_text(
            text=self.text, start=start, end=end
        )
        new_selection = self.selection & limit_selector
        self.selection = new_selection
        return None

    def select_more_text_at_current_node(
        self, added_selection: TextPositionSet
    ) -> None:
        """Select more text at this Enactment's node, not in child nodes."""
        new_selection = self.enactment.limit_selection_to_current_node(added_selection)
        self.selection = self.selection + new_selection
        return None

    def _update_text_at_included_node(
        self, other: EnactmentPassage
    ) -> Tuple[bool, bool]:
        """Recursively search child nodes for one that can be updated by `other`."""
        if self.node == other.node:
            found_node = True
            if self.text == other.text:
                self.select_more_text_in_current_branch(other.selection)
            else:
                self.select_more_text_from_changed_version(other)
            return found_node, True
        for selector in other.as_quotes():
            self.select_more(selector)
        return False, False

    def _add_passage_at_included_node(
        self, other: EnactmentPassage
    ) -> EnactmentPassage:
        """Add a selection of text at the same citation or at a child of self's citation."""

        if self >= other:
            return self

        copy_of_self = deepcopy(self)
        copy_of_self._update_text_at_included_node(other)
        return copy_of_self

    def implies(self, other: Union[Enactment, EnactmentPassage]) -> bool:
        """Test whether ``self`` has all the text passages of ``other``."""
        if not isinstance(other, (Enactment, EnactmentPassage)):
            raise TypeError(
                f"Cannot compare {self.__class__.__name__} and {other.__class__.__name__} for implication."
            )
        self_selected_passages = self.text_sequence(include_nones=False)
        other_selected_passages = other.text_sequence(include_nones=False)
        return self_selected_passages >= other_selected_passages

    def __add__(self, other: Union[Enactment, EnactmentPassage]) -> EnactmentPassage:

        if isinstance(other, Enactment):
            other = other.select_all()

        if not isinstance(other, self.__class__):
            copy_of_self = deepcopy(self)
            copy_of_self.select_more(other)
            return copy_of_self

        if other.node.startswith(self.node):
            return self._add_passage_at_included_node(other)
        elif self.node.startswith(other.node):
            return other._add_passage_at_included_node(self)

        raise ValueError(
            "Can't add selected text from two different Enactments "
            "when neither is a descendant of the other."
        )

    def __ge__(self, other: Union[Enactment, EnactmentPassage]) -> bool:
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
        start: int = 0,
        end: Optional[int] = None,
    ) -> None:
        """Select text from Enactment."""
        selection_set = self.enactment.make_selection(
            selection=selection, start=start, end=end
        )
        self.selection = selection_set
        return None

    def clear_selection(self) -> None:
        """Deselect any Enactment text, including in child nodes."""
        self.selection = TextPositionSet()

    def select_more_text_from_changed_version(self, other: EnactmentPassage) -> None:
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
        incoming_quote_selectors = other.as_quotes()
        incoming_position_selectors = []
        for quote_selector in incoming_quote_selectors:
            position = quote_selector.as_unique_position(self.text)
            if position:
                incoming_position_selectors.append(position)
        self.select_more_text_in_current_branch(
            TextPositionSet(positions=incoming_position_selectors)
        )

    def selected_text(self) -> str:
        """
        Return this provision's text that is within the ranges described by self.selection.

        Based on creating an :class:`anchorpoint.textsequences.TextSequence` from this Enactment's
        text content and the ranges in its selection attribute.
        """
        text_sequence = self.text_sequence()
        return str(text_sequence)

    def text_sequence(self, include_nones: bool = True) -> TextSequence:
        """
        List the phrases in the Enactment selected by TextPositionSelectors.

        :param include_nones:
            Whether the list of phrases should include `None` to indicate a block of
            unselected text
        """
        return self.selection.as_text_sequence(
            text=self.enactment.text, include_nones=include_nones
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
            selection = self.enactment.convert_selection_to_set(selection)

        self.selection += selection
        self.selection = self.selection.add_margin(text=self.text, margin_width=4)
        self.enactment.raise_error_for_extra_selector(selection)

    def select_more_text_in_current_branch(
        self, added_selection: TextPositionSet
    ) -> None:
        """Select more text within this Enactment's tree_selection, including child nodes."""
        new_selection = self.selection + added_selection
        self.selection = new_selection
        return None

    def means(self, other: EnactmentPassage) -> bool:
        r"""
        Find whether meaning of ``self`` is equivalent to that of ``other``.

        ``Self`` must be neither broader nor narrower than ``other`` to return True.

        :returns:
            whether ``self`` and ``other`` represent the same text
            issued by the same sovereign in the same level of
            :class:`Enactment`\.
        """
        if not isinstance(other, (EnactmentPassage, Enactment)):
            raise TypeError(
                f"Cannot compare {self.__class__.__name__} and {other.__class__.__name__} for same meaning."
            )
        self_selected_passages = self.text_sequence()
        other_selected_passages = other.text_sequence()
        return self_selected_passages.means(other_selected_passages)


class AnchoredEnactmentPassage(BaseModel):
    """A quoted Enactment passage with anchors to an external document.

    :param passage:
        an EnactmentPassage with selectors indicating which part
        of the Enactment is being referenced.

    :param anchor:
        anchors to text in an external document that references
        the EnactmentPassage
    """

    passage: EnactmentPassage
    anchors: TextPositionSet


def consolidate_enactments(
    enactments: Sequence[Union[Enactment, EnactmentPassage]]
) -> List[EnactmentPassage]:
    r"""
    Consolidate any overlapping :class:`Enactment`\s in a :class:`list`.

    :param enactments:
        a list of :class:`Enactment`\s that may include overlapping
        legislative text within the same section

    :returns:
        a list of :class:`Enactment`\s without overlapping text
    """
    consolidated: List[EnactmentPassage] = []
    passages: List[EnactmentPassage] = [
        item.select_all() if isinstance(item, Enactment) else item
        for item in enactments
    ]
    while passages:
        match_made = False
        left = passages.pop()
        for right in passages:
            try:
                combined = left + right
                passages.remove(right)
                passages.append(combined)
                match_made = True
                break
            except (ValueError, TypeError, TextSelectionError):
                pass
        if not match_made:
            consolidated.append(left)
    return consolidated
