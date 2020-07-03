from marshmallow import Schema, fields, post_load, validate, EXCLUDE

from anchorpoint.textselectors import (
    TextQuoteSelector,
    TextPositionSelector,
    TextPositionSet,
)

from legislice.enactments import Enactment


class QuoteSelectorSchema(Schema):

    __model__ = TextQuoteSelector
    exact = fields.Str(missing=None)
    prefix = fields.Str(missing=None)
    suffix = fields.Str(missing=None)

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)


class PositionSelectorSchema(Schema):

    __model__ = TextPositionSelector
    start = fields.Int()
    end = fields.Int(missing=None)
    include_start = fields.Bool(missing=True)
    include_end = fields.Bool(missing=False)

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)


class EnactmentSchema(Schema):
    """Schema for passages from legislation."""

    __model__ = Enactment
    node = fields.Url(relative=True)
    heading = fields.Str()
    content = fields.Str()
    start_date = fields.Date()
    end_date = fields.Date(missing=None)
    children = fields.List(fields.Nested(lambda: EnactmentSchema()))
    selection = fields.Nested(PositionSelectorSchema, many=True, missing=True)

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_object(self, data, **kwargs):

        return self.__model__(**data)
