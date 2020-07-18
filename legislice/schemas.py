from datetime import date
from typing import Dict

from anchorpoint.schemas import SelectorSchema
from marshmallow import Schema, fields, post_load, pre_load, EXCLUDE

from legislice.enactments import Enactment, LinkedEnactment


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

    @pre_load
    def accept_selector_outside_list(self, data, **kwargs):
        if isinstance(data.get("selection"), Dict):
            data["selection"] = [data["selection"]]
        return data


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

    @pre_load
    def accept_selector_outside_list(self, data, **kwargs):
        if isinstance(data.get("selection"), Dict):
            data["selection"] = [data["selection"]]
        return data

    @post_load
    def make_object(self, data, **kwargs):

        return self.__model__(**data)
