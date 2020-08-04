from copy import deepcopy
from datetime import date
from typing import Dict, List, Union

from anchorpoint.schemas import SelectorSchema
from marshmallow import Schema, fields, post_load, pre_load, EXCLUDE, ValidationError

from legislice.enactments import Enactment, LinkedEnactment, RawEnactment
from legislice.name_index import EnactmentIndex


def enactment_needs_api_update(data: RawEnactment) -> bool:
    """Determine if JSON representation of Enactment needs to be supplemented from API."""
    if not data.get("node"):
        raise ValueError(
            '"data" must contain a "node" field '
            "with a citation path to a legislative provision, "
            'for example "/us/const/amendment/IV"'
        )
    if (
        data.get("heading") is None
        or data.get("content") is None
        or data.get("start_date") is None
    ):
        return True
    return False


class ExpandableSchema(Schema):
    """Base schema for classes that can be cross-referenced by name in input JSON."""

    def get_indexed_enactment(self, data, **kwargs):
        """Replace data to load with any object with same name in "enactment_index"."""
        if isinstance(data, str):
            name_to_retrieve = data
        elif data.get("name") and enactment_needs_api_update(data):
            name_to_retrieve = data["name"]
        else:
            return data

        mentioned = self.context.get("enactment_index") or EnactmentIndex()
        return deepcopy(mentioned.get_by_name(name_to_retrieve))

    def consume_type_field(self, data, **kwargs):
        """Verify that type field is correct and then get rid of it."""
        if data.get("type"):
            ty = data.pop("type").lower()
            if ty != self.__model__.__name__.lower():
                raise ValidationError(
                    f'type field "{ty} does not match model type {self.__model__}'
                )
        return data

    def wrap_single_element_in_list(self, data: Dict, many_element: str):
        """Make a specified field a list if it isn't already a list."""
        if data.get(many_element) is None:
            data[many_element] = []
        elif not isinstance(data[many_element], list):
            data[many_element] = [data[many_element]]
        return data

    @pre_load
    def format_data_to_load(self, data: Union[str, Dict], **kwargs) -> Dict:
        """Expand data if it was just a name reference in the JSON input."""
        data = self.consume_type_field(data)
        return data

    @post_load
    def make_object(self, data, **kwargs) -> Enactment:
        """Make Legislice object out of whatever data has been loaded."""
        return self.__model__(**data)


class LinkedEnactmentSchema(ExpandableSchema):
    """Schema for passages from legislation without the full text of child nodes."""

    __model__ = LinkedEnactment
    node = fields.Url(relative=True, required=True)
    heading = fields.Str(required=True)
    content = fields.Str(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(missing=None)
    children = fields.List(fields.Url(relative=False))
    selection = fields.Nested(SelectorSchema, many=True, missing=list)
    anchors = fields.Nested(SelectorSchema, many=True, missing=list)

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_object(self, data, **kwargs):
        if data.get("selection"):
            data["selection"] = [item for item in data["selection"] if item is not None]

        return self.__model__(**data)

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

    @pre_load
    def format_data_to_load(self, data, **kwargs):
        """Prepare Enactment to load."""
        data = self.get_indexed_enactment(data)
        data = self.wrap_single_element_in_list(data, "selection")
        data = self.move_selector_fields(data)
        data = self.wrap_single_element_in_list(data, "anchors")
        data = self.consume_type_field(data)
        return data


class EnactmentSchema(LinkedEnactmentSchema):
    """Schema for passages from legislation."""

    __model__ = Enactment
    children = fields.List(fields.Nested(lambda: EnactmentSchema()))

    class Meta:
        unknown = EXCLUDE


def get_schema_for_node(path: str):
    if path.count("/") < 4:
        return LinkedEnactmentSchema
    return EnactmentSchema
