"""
Schemas for loading Enactments from user-generated YAML.

These schemas are more cumbersome than the schemas for serialized
objects or API responses, but they allow more abbreviations and omissions.
"""

from typing import Dict, Type, Union

from anchorpoint.schemas import SelectorSchema
from marshmallow import fields, post_load, pre_load, EXCLUDE

from legislice.enactments import (
    Enactment,
    LinkedEnactment,
    RawEnactment,
)

from legislice.schemas import (
    CrossReferenceSchema,
    TextVersionSchema,
    LinkedEnactmentSchema,
    EnactmentSchema,
)


class ExpandableLinkedEnactmentSchema(LinkedEnactmentSchema):
    """Schema for passages from legislation without the full text of child nodes."""

    __model__: Union[Type[Enactment], Type[LinkedEnactment]] = LinkedEnactment
    node = fields.Url(relative=True, required=True)
    heading = fields.Str(required=True)
    text_version = fields.Nested(TextVersionSchema, required=False, missing=None)
    start_date = fields.Date(required=True)
    end_date = fields.Date(missing=None)
    known_revision_date = fields.Boolean()
    selection = fields.Nested(SelectorSchema, many=True, missing=list)
    anchors = fields.Nested(SelectorSchema, many=True, missing=list)
    citations = fields.Nested(CrossReferenceSchema, many=True, missing=list)
    children = fields.List(fields.Url(relative=False))

    class Meta:
        """Exclude unknown fields from schema."""

        unknown = EXCLUDE
        ordered = True

    def wrap_single_element_in_list(self, data: Dict, many_element: str):
        """Make a specified field a list if it isn't already a list."""
        if data.get(many_element) is None:
            data[many_element] = []
        elif not isinstance(data[many_element], list):
            data[many_element] = [data[many_element]]
        return data

    def move_selector_fields(self, data: RawEnactment, **kwargs):
        """
        Nest fields used for :class:`SelectorSchema` model.

        If the fields are already nested, they need not to be moved.

        The fields can only be moved into a "selector" field with a dict
        value, not a "selectors" field with a list value.
        """

        selector_field_names = ["text", "exact", "prefix", "suffix", "start", "end"]
        new_selector = {}
        for name in selector_field_names:
            if data.get(name):
                new_selector[name] = data[name]
                del data[name]
        if new_selector:
            data["selection"].append(new_selector)
        return data

    def nest_content_in_textversion(self, data):
        """Correct user-generated data omitting a layer of nesting."""
        if data.get("content"):
            if not data.get("text_version"):
                data["text_version"] = {}
            data["text_version"]["content"] = data["content"]
        data.pop("content", None)
        return data

    @pre_load
    def format_data_to_load(self, data, **kwargs):
        """Prepare Enactment to load."""
        data = self.nest_content_in_textversion(data)
        data = self.wrap_single_element_in_list(data, "selection")
        data = self.move_selector_fields(data)
        data = self.wrap_single_element_in_list(data, "anchors")
        data = self.is_revision_date_known(data)
        return data

    @post_load
    def make_object(self, data, **kwargs):
        """Make Linked Enactment, omitting any text selectors."""
        if data.get("selection"):
            data["selection"] = [item for item in data["selection"] if item is not None]

        return self.__model__(**data)


class ExpandableEnactmentSchema(ExpandableLinkedEnactmentSchema):
    """Schema for passages from legislation."""

    __model__ = Enactment
    children = fields.List(fields.Nested(lambda: ExpandableEnactmentSchema()))
    heading = fields.Str(missing="")

    class Meta:
        """Exclude unknown fields from schema."""

        unknown = EXCLUDE
        ordered = True


def get_schema_for_node(path: str, use_text_expansion: bool = False):
    """Decide whether to load Enactment with descendant nodes or only with links to child nodes."""
    if use_text_expansion:
        if path.count("/") < 4:
            return ExpandableLinkedEnactmentSchema
        return ExpandableEnactmentSchema

    if path.count("/") < 4:
        return LinkedEnactmentSchema
    return EnactmentSchema
