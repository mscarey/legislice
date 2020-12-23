from copy import deepcopy
import datetime
from typing import Dict, Union

from anchorpoint.schemas import SelectorSchema
from marshmallow import Schema, fields, post_load, pre_load, EXCLUDE

from legislice.enactments import (
    Enactment,
    InboundReference,
    LinkedEnactment,
    RawEnactment,
    CrossReference,
    TextVersion,
    CitingProvisionLocation,
)
from legislice.name_index import EnactmentIndex


def enactment_needs_api_update(data: RawEnactment) -> bool:
    """Determine if JSON representation of Enactment needs to be supplemented from API."""
    if not data.get("node"):
        raise ValueError(
            '"data" must contain a "node" field '
            "with a citation path to a legislative provision, "
            'for example "/us/const/amendment/IV"'
        )
    if data.get("heading") is None or data.get("start_date") is None:
        return True
    if data.get("content") is None and data.get("text_version") is None:
        return False


class CitingProvisionLocationSchema(Schema):
    __model__ = CitingProvisionLocation

    heading = fields.Str()
    node = fields.Str()
    start_date = fields.Date()

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_object(self, data, **kwargs) -> CitingProvisionLocation:
        return self.__model__(**data)


class InboundReferenceSchema(Schema):
    __model__ = InboundReference

    content = fields.Str()
    reference_text = fields.Str()
    target_uri = fields.Str()
    locations = fields.Nested(CitingProvisionLocationSchema, many=True)

    class Meta:
        unknown = EXCLUDE

    @pre_load
    def format_data_to_load(
        self, data: Dict[str, Union[Dict[str, str], str]], **kwargs
    ) -> Dict:

        reference_text = ""
        for citation in data["citations"]:
            if citation["target_uri"] == data["target_uri"]:
                reference_text = citation["reference_text"]
        data["reference_text"] = reference_text

        return data

    @post_load
    def make_object(self, data, **kwargs) -> InboundReference:
        return self.__model__(**data)


class CrossReferenceSchema(Schema):
    __model__ = CrossReference

    target_uri = fields.Str(required=True)
    target_url = fields.Url(relative=False, required=True)
    reference_text = fields.Str(required=True)
    target_node = fields.Int(required=False)

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_object(self, data, **kwargs) -> CrossReference:
        return self.__model__(**data)


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

    def wrap_single_element_in_list(self, data: Dict, many_element: str):
        """Make a specified field a list if it isn't already a list."""
        if data.get(many_element) is None:
            data[many_element] = []
        elif not isinstance(data[many_element], list):
            data[many_element] = [data[many_element]]
        return data

    @post_load
    def make_object(self, data, **kwargs):
        if data.get("selection"):
            data["selection"] = [item for item in data["selection"] if item is not None]

        return self.__model__(**data)


class TextVersionSchema(Schema):
    __model__ = TextVersion
    content = fields.Str(required=True)

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)


class LinkedEnactmentSchema(ExpandableSchema):
    """Schema for passages from legislation without the full text of child nodes."""

    __model__ = LinkedEnactment
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
        unknown = EXCLUDE
        ordered = True

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
        if data.get("content"):
            if not data.get("text_version"):
                data["text_version"] = {}
            data["text_version"]["content"] = data["content"]
        data.pop("content", None)
        return data

    def is_revision_date_known(self, data):
        if not self.context.get("coverage"):
            data["known_revision_date"] = False
        elif self.context["coverage"]["earliest_in_db"] and (
            self.context["coverage"]["earliest_in_db"]
            < datetime.date.fromisoformat(data["start_date"])
        ):
            data["known_revision_date"] = True
        elif (
            self.context["coverage"]["earliest_in_db"]
            and self.context["coverage"]["first_published"]
            and (
                self.context["coverage"]["earliest_in_db"]
                <= self.context["coverage"]["first_published"]
            )
        ):
            data["known_revision_date"] = True
        else:
            data["known_revision_date"] = False
        return data

    @pre_load
    def format_data_to_load(self, data, **kwargs):
        """Prepare Enactment to load."""
        data = self.get_indexed_enactment(data)
        data = self.nest_content_in_textversion(data)
        data = self.wrap_single_element_in_list(data, "selection")
        data = self.move_selector_fields(data)
        data = self.wrap_single_element_in_list(data, "anchors")
        data = self.is_revision_date_known(data)
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
