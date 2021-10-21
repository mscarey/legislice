"""TypedDict data structures used for communicating between an API and Legislice."""

from datetime import date
from typing import Any, List, Optional, TypedDict


class RawPositionSelector(TypedDict):
    """Data for a TextPositionSelector."""

    start: int
    end: Optional[int]


class RawQuoteSelector(TypedDict):
    """Data for a TextQuoteSelector."""

    prefix: str
    exact: str
    suffix: str


class RawSelectorSet(TypedDict):
    """
    Data for a set of Anchorpoint selectors.

    Used in Legislice to specify the cited part of an Enactment.
    """

    positions: Optional[List[RawPositionSelector]]
    quotes: Optional[List[RawQuoteSelector]]


class CrossReferenceDict(TypedDict):
    """A citation from the provision that is the subject of the API call, leading to another provision."""

    target_uri: str
    target_url: str
    reference_text: str
    target_node: Optional[int]


class RawEnactment(TypedDict):
    """Data for creating an Enactment."""

    heading: str
    start_date: Optional[str]
    node: str
    url: str
    end_date: Optional[str]
    content: str
    children: List[Any]  # cyclic definition not allowed for mypy
    citations: List[CrossReferenceDict]
    earliest_in_db: Optional[date]
    first_published: Optional[date]


class RawEnactmentPassage(TypedDict):
    """Data for creating an EnactmentPassage."""

    enactment: RawEnactment
    selection: RawSelectorSet


class CitingProvisionLocationDict(TypedDict):
    """
    Location of provision citing to the provision that is the subject of the API call.

    Can occur as part of an FetchedCitationDict created by
    a call to the `citations_to` API endpoint.
    """

    heading: str
    start_date: str
    node: str


class FetchedCitationDict(TypedDict):
    """
    Information about a statute that cites the subject of the API call.

    Created by a call to the `citations_to` API endpoint.
    """

    content: str
    locations: List[CitingProvisionLocationDict]
    citations: List[CrossReferenceDict]
    url: str
    target_uri: Optional[str]


class InboundReferenceDict(TypedDict):
    """
    Information about statute that cites the subject of the API call, with text of reference.

    Created by finding the relevant citation in a FetchedCitationDict, and
    then pulling the `reference` field from within the citation.
    """

    content: str
    locations: List[CitingProvisionLocationDict]
    citations: List[CrossReferenceDict]
    url: str
    target_uri: str
    reference_text: Optional[str]


class PublicationCoverage(TypedDict):
    """Available dates for a publication covered in an API's database."""

    uri: str
    latest_heading: str
    first_published: date
    earliest_in_db: date
    latest_in_db: date
