"""Utility for downloading and comparing the text of statutes and constitutional provisions."""

from anchorpoint.textselectors import TextQuoteSelector, TextPositionSelector
from anchorpoint.textselectors import TextPositionSet

from legislice.enactments import Enactment
from legislice.citations import Citation
from legislice.download import Client
from legislice.groups import EnactmentGroup

__version__ = "0.7.0"
