"""Citations to codified citations."""

from datetime import date
from enum import IntEnum
import json
from typing import Dict, List, Optional, Tuple, Union

from pydantic.class_validators import validator, root_validator
from pydantic import BaseModel, Field


class CodeLevel(IntEnum):
    """Identifier for the type of legislative code."""

    CONSTITUTION = 1
    STATUTE = 2
    REGULATION = 3
    COURT_RULE = 4


# Path parts known to indicate the level of law they refer to.
KNOWN_CODES: Dict[str, Dict[str, Tuple[str, CodeLevel]]] = {
    "test": {"acts": ("Test Acts", CodeLevel.STATUTE)},
    "us": {
        "const": ("U.S. Const.", CodeLevel.CONSTITUTION),
        "usc": ("U.S. Code", CodeLevel.STATUTE),
        "cfr": ("CFR", CodeLevel.REGULATION),
    },
    "us-ca": {
        "const": ("Cal. Const.", CodeLevel.CONSTITUTION),
        "code": ("Cal. Codes", CodeLevel.STATUTE),
        "ccr": ("Cal. Code Regs.", CodeLevel.REGULATION),
        "roc": ("Cal. Rules of Court", CodeLevel.COURT_RULE),
    },
}


def identify_code(jurisdiction: str, code: str) -> Tuple[str, CodeLevel]:
    """Find code name and type based on USLM citation parts."""
    try:
        sovereign = KNOWN_CODES[jurisdiction]
    except KeyError:
        raise KeyError(f'"{jurisdiction}" is not a known jurisdiction identifier')

    try:
        code_name, code_level = sovereign[code]
    except KeyError:
        raise KeyError(f'"{code}" is not a known code identifier')

    return code_name, code_level


class Citation(BaseModel):
    r"""
    A citation style for referring to an :class:`~legislice.enactments.Enactment` in written text.

    Intended for use with `Citation Style Language
    (CSL) <https://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html>`_.
    """

    jurisdiction: str
    code: str
    code_level_name: Optional[str] = None
    volume: Optional[str] = None
    section: Optional[str] = None
    revision_date: Optional[date] = None
    type: str = Field("legislation", const=True)

    @root_validator(pre=True)
    def validate_code(cls, obj):
        """Standardize the code name for the styled citation."""
        if obj.get("code"):
            obj["code"], obj["code_level_name"] = identify_code(
                jurisdiction=obj["jurisdiction"], code=obj["code"]
            )
        return obj

    @validator("volume")
    def validate_volume(cls, value):
        """Make sure the "title" identifier for the styled citation doesn't start with "t"."""
        if value:
            value = value.lstrip("t")
        return value

    @validator("section")
    def validate_section(cls, value):
        """Make sure the "section" part of the styled citation starts with the right abbreviation."""
        if value and not value.startswith("sec. "):
            value = "sec. " + value.lstrip("s")
        return value

    @staticmethod
    def csl_date_format(revision_date: date) -> Dict[str, List[List[Union[str, int]]]]:
        """Convert event date to Citation Style Language format."""
        return {
            "date-parts": [
                [
                    str(revision_date.year),
                    revision_date.month,
                    revision_date.day,
                ]
            ]
        }

    def __str__(self):
        name = f"{self.volume} {self.code} {self.section}"
        if self.revision_date:
            name += f" ({self.revision_date.year})"
        return name.replace("sec.", "§")

    def csl_dict(self) -> Dict[str, Union[str, int, List[List[Union[str, int]]]]]:
        """Return citation as a Citation Style Language object."""
        result = self.dict()
        result["container-title"] = result.pop("code", None)
        event_date = result.pop("revision_date", None)
        if event_date:
            result["event-date"] = self.csl_date_format(event_date)

        return result

    def csl_json(self) -> str:
        """Return citation as Citation Style Language JSON."""
        obj = self.csl_dict()
        return json.dumps(obj)
