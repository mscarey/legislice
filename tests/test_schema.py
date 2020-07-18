from anchorpoint.textselectors import TextPositionSelector
from marshmallow import ValidationError
import pytest

from legislice.schemas import (
    EnactmentSchema,
    LinkedEnactmentSchema,
    SelectorSchema,
)


class TestLoadSelector:
    def test_schema_loads_position_selector(self):
        schema = SelectorSchema()
        data = {"start": 0, "end": 12}
        result = schema.load(data)
        assert isinstance(result, TextPositionSelector)

    def test_selector_text_split(self):
        schema = SelectorSchema()
        data = {"text": "process, system,|method of operation|, concept, principle"}
        result = schema.load(data)
        assert result.exact.startswith("method")

    def test_selector_from_string(self):
        data = "eats,|shoots,|and leaves"
        schema = SelectorSchema()
        result = schema.load(data)
        assert result.exact == "shoots,"

    def test_selector_from_string_without_split(self):
        data = "promise me not to omit a single word"
        schema = SelectorSchema()
        result = schema.load(data)
        assert result.exact.startswith("promise")

    def test_selector_from_string_split_wrongly(self):
        data = "eats,|shoots,|and leaves|"
        schema = SelectorSchema()
        with pytest.raises(ValueError):
            _ = schema.load(data)


class TestLoadEnactment:
    def test_load_nested_enactment(self, section6d):
        schema = EnactmentSchema()
        result = schema.load(section6d)
        assert result.heading.startswith("Waiver")

    def test_enactment_with_nested_selectors(self, section_11_subdivided):
        schema = EnactmentSchema()
        section_11_subdivided["selection"] = [{"start": 0}]
        for child in section_11_subdivided["children"]:
            child["selection"] = []
        section_11_subdivided["children"][1]["selection"] = [{"start": 0, "end": 12}]
        result = schema.load(section_11_subdivided)
        answer = "The Department of Beards may issue licenses to such...hairdressers..."
        assert result.selected_text() == answer

    def test_selector_not_wrapped_in_list(self, section_11_together):
        schema = EnactmentSchema()
        section_11_together["selection"] = {"start": 4, "end": 24}
        result = schema.load(section_11_together)
        assert result.selected_text() == "...Department of Beards..."

    def test_load_with_text_quote_selector(self, section_11_together):
        schema = EnactmentSchema()
        section_11_together["selection"] = [{"exact": "Department of Beards"}]
        result = schema.load(section_11_together)
        assert result.selected_text() == "...Department of Beards..."


class TestLoadLinkedEnactment:
    def test_load_linked_enactment(self):
        schema = LinkedEnactmentSchema()
        data = {
            "children": [
                "https://authorityspoke.com/api/v1/us/const/",
                "https://authorityspoke.com/api/v1/us/usc/",
            ],
            "content": "",
            "end_date": None,
            "heading": "United States Legislation",
            "node": "/us",
            "parent": None,
            "start_date": "1776-07-04",
            "url": "https://authorityspoke.com/api/v1/us/const/",
        }
        result = schema.load(data)
        assert result.children[0] == "https://authorityspoke.com/api/v1/us/const/"
