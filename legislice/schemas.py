from datetime import date
from typing import Dict, Tuple, Union

from marshmallow import Schema, fields, post_load, pre_load, EXCLUDE
from marshmallow import validate, ValidationError

from anchorpoint.textselectors import (
    TextQuoteSelector,
    TextPositionSelector,
    TextPositionSet,
)

from legislice.enactments import Enactment, LinkedEnactment


def split_anchor_text(text: str) -> Tuple[str, ...]:
    """
    Break up shorthand text selector format into three fields.

    Tries to break up the  string into :attr:`~TextQuoteSelector.prefix`,
    :attr:`~TextQuoteSelector.exact`,
    and :attr:`~TextQuoteSelector.suffix`, by splitting on the pipe characters.

    :param text: a string or dict representing a text passage

    :returns: a tuple of the three values
    """

    if text.count("|") == 0:
        return ("", text, "")
    elif text.count("|") == 2:
        return tuple([*text.split("|")])
    raise ValidationError(
        "If the 'text' field is included, it must be either a dict "
        + "with one or more of 'prefix', 'exact', and 'suffix' "
        + "a string containing no | pipe "
        + "separator, or a string containing two pipe separators to divide "
        + "the string into 'prefix', 'exact', and 'suffix'."
    )


class SelectorSchema(Schema):

    __model__ = TextQuoteSelector
    exact = fields.Str(missing=None)
    prefix = fields.Str(missing=None)
    suffix = fields.Str(missing=None)

    start = fields.Int()
    end = fields.Int(optional=True)
    include_start = fields.Bool(missing=True)
    include_end = fields.Bool(missing=False)

    @pre_load
    def expand_anchor_shorthand(
        self, data: Union[str, Dict[str, str]], **kwargs
    ) -> Dict[str, str]:
        """
        Convert input from shorthand format to normal selector format.
        """
        if isinstance(data, str):
            data = {"text": data}
        text = data.get("text")
        if text:
            data["prefix"], data["exact"], data["suffix"] = split_anchor_text(text)
            del data["text"]
        return data

    @post_load
    def make_object(self, data, **kwargs):
        if data.get("exact") or data.get("prefix") or data.get("suffix"):
            model = TextQuoteSelector
            for unwanted in ("start", "end", "include_start", "include_end"):
                data.pop(unwanted, None)
        else:
            model = TextPositionSelector
            for unwanted in ("exact", "prefix", "suffix"):
                data.pop(unwanted, None)
        return model(**data)


class PositionSelectorSchema(Schema):

    __model__ = TextPositionSelector

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)


class LinkedEnactmentSchema(Schema):
    """Schema for passages from legislation without the full text of child nodes."""

    __model__ = LinkedEnactment
    node = fields.Url(relative=True)
    heading = fields.Str()
    content = fields.Str()
    start_date = fields.Date(missing=date.today)
    end_date = fields.Date(missing=None)
    children = fields.List(fields.Url(relative=False))
    selection = fields.Nested(SelectorSchema, many=True, missing=True)

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_object(self, data, **kwargs):

        return self.__model__(**data)


class EnactmentSchema(Schema):
    """Schema for passages from legislation."""

    __model__ = Enactment
    node = fields.Url(relative=True)
    heading = fields.Str()
    content = fields.Str()
    start_date = fields.Date(missing=date.today)
    end_date = fields.Date(missing=None)
    children = fields.List(fields.Nested(lambda: EnactmentSchema()))
    selection = fields.Nested(SelectorSchema, many=True, missing=True)

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_object(self, data, **kwargs):

        return self.__model__(**data)
