"""Citations to codified citations."""

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple, Union

from marshmallow import Schema, fields, post_dump

# Path parts known to indicate the level of law they refer to.
KNOWN_CODES = {
    "test": {"acts": ["Test Acts", "S"]},
    "us": {
        "const": ["U.S. Const.", "C"],
        "usc": ["U.S. Code", "S"],
        "cfr": ["CFR", "R"],
    },
}

CODE_LEVEL_NAMES = {"C": "constitution", "S": "statute", "R": "regulation"}


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

    code_level_name = CODE_LEVEL_NAMES[code_level]
    return code_name, code_level_name


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


@dataclass
class Citation:
    r"""
    A citation style for referring to an :class:`~legislice.enactments.Enactment` in written text.

    Intended for use with `Citation Style Language (CSL) <https://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html>`_.
    """

    def __init__(
        self,
        jurisdiction: str,
        code: Optional[str] = None,
        volume: Optional[str] = None,
        section: Optional[str] = None,
        revision_date: Optional[date] = None,
    ) -> None:
        """Convert identifier parts to CSL format."""
        self.jurisdiction = jurisdiction

        if code:
            code, code_level_name = identify_code(jurisdiction=jurisdiction, code=code)
        self.code = code

        if volume:
            volume = volume.lstrip("t")
        self.volume = volume

        if section:
            section = "sec. " + section.lstrip("s")
        self.section = section

        self.revision_date = revision_date

    def __str__(self):
        name = f"{self.volume} {self.code} {self.section}"
        if self.revision_date:
            name += f" ({self.revision_date.year})"
        return name.replace("sec.", "§")

    def as_dict(self) -> str:
        """Dump Citation Style Language data as Python object."""
        schema = CitationSchema()
        return schema.dump(self)

    def as_json(self) -> str:
        """Dump Citation Style Language data as JSON."""
        schema = CitationSchema()
        return schema.dumps(self)
