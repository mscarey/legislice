"""Citations to codified citations."""

from datetime import date
from enum import IntEnum
import json
from typing import Dict, List, Optional, Tuple, Union

from marshmallow import Schema, fields
from pydantic.class_validators import validator, root_validator
from pydantic.main import BaseModel


class CodeLevel(IntEnum):
    CONSTITUTION = 1
    STATUTE = 2
    REGULATION = 3
    COURT_RULE = 4


# Path parts known to indicate the level of law they refer to.
KNOWN_CODES = {
    "test": {"acts": ["Test Acts", CodeLevel.STATUTE]},
    "us": {
        "const": ["U.S. Const.", CodeLevel.CONSTITUTION],
        "usc": ["U.S. Code", CodeLevel.STATUTE],
        "cfr": ["CFR", CodeLevel.REGULATION],
    },
    "us-ca": {
        "const": ["Cal. Const.", CodeLevel.CONSTITUTION],
        "code": ["Cal. Codes", CodeLevel.STATUTE],
        "ccr": ["Cal. Code Regs.", CodeLevel.REGULATION],
        "roc": ["Cal. Rules of Court", CodeLevel.COURT_RULE],
    },
}


def identify_code(jurisdiction: str, code: str) -> Tuple[str, str]:
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


class CitationSchema(Schema):
    """Schema for legislative citations."""

    document_type = fields.Str(data_key="type", default="legislation", dump_only=True)
    jurisdiction = fields.Str(required=True)
    code = fields.Str(data_key="container-title", required=False)
    volume = fields.Str(required=False)
    section = fields.Str(required=False)
    revision_date = fields.Date(default=None, load_only=True)
    event_date = fields.Method(
        data_key="event-date", serialize="dump_event_date", dump_only=True
    )

    class Meta:
        ordered = True

    def dump_event_date(self, obj) -> Optional[Dict[str, List[List[Union[str, int]]]]]:
        """Serialize date as three numbers in "date-parts" field."""
        if not obj.revision_date:
            return None

        return {
            "date-parts": [
                [
                    str(obj.revision_date.year),
                    obj.revision_date.month,
                    obj.revision_date.day,
                ]
            ]
        }


class Citation(BaseModel):
    r"""
    A citation style for referring to an :class:`~legislice.enactments.Enactment` in written text.

    Intended for use with `Citation Style Language
    (CSL) <https://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html>`_.
    """

    jurisdiction: str
    code: Optional[str] = None
    code_level_name: Optional[str] = None
    volume: Optional[str] = None
    section: Optional[str] = None
    revision_date: Optional[date] = None

    @root_validator(pre=True)
    def validate_code(cls, obj):
        if obj.get("code"):
            obj["code"], obj["code_level_name"] = identify_code(
                jurisdiction=obj["jurisdiction"], code=obj["code"]
            )
        return obj

    @validator("volume")
    def validate_volume(cls, value):
        if value:
            value = value.lstrip("t")
        return value

    @validator("section")
    def validate_section(cls, value):
        if value and not value.startswith("sec. "):
            value = "sec. " + value.lstrip("s")
        return value

    def revision_date_parts(self) -> List[List[Union[str, int]]]:
        """Return date as three numbers in "date-parts" field."""
        if not self.revision_date:
            return []

        return [
            [
                str(self.revision_date.year),
                self.revision_date.month,
                self.revision_date.day,
            ]
        ]

    def __str__(self):
        name = f"{self.volume} {self.code} {self.section}"
        if self.revision_date:
            name += f" ({self.revision_date.year})"
        return name.replace("sec.", "§")

    def csl_dict(self) -> Dict[str, Union[str, int, List[List[Union[str, int]]]]]:
        """Return citation as a Citation Style Language object."""
        schema = CitationSchema()
        return schema.dump(self)

    def csl_json(self) -> str:
        """Return citation as Citation Style Language JSON."""
        obj = self.csl_dict()
        return json.dumps(obj)
