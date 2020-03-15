from marshmallow import Schema, fields, post_load, validate, EXCLUDE

from legislice.enactments import Enactment


class EnactmentSchema(Schema):
    """Schema for passages from legislation."""

    __model__ = Enactment
    node = fields.Url(relative=True)
    heading = fields.Str()
    content = fields.Str()
    start_date = fields.Date()
    end_date = fields.Date(missing=None)
    children = fields.List(fields.Nested(lambda: EnactmentSchema()))

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)
