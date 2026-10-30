"""Utility for downloading and comparing the text of statutes and constitutional provisions."""

from anchorpoint.textselectors import (
    TextPositionSelector,
    TextPositionSet,
    TextQuoteSelector,
)

from legislice.citations import Citation
from legislice.download import Client
from legislice.enactments import Enactment
from legislice.groups import EnactmentGroup

__version__ = "0.8.1"
__all__ = [
    "Citation",
    "Client",
    "Enactment",
    "EnactmentGroup",
    "TextPositionSelector",
    "TextPositionSet",
    "TextQuoteSelector",
]
