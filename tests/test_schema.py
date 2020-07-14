from anchorpoint.textselectors import TextPositionSelector

from legislice.schemas import (
    EnactmentSchema,
    PositionSelectorSchema,
    QuoteSelectorSchema,
)


class TestLoadSelector:
    def test_schema_loads_position_selector(self):
        schema = PositionSelectorSchema()
        data = {"start": 0, "end": 12}
        result = schema.load(data)
        assert isinstance(result, TextPositionSelector)

    def test_selector_text_split(self):
        schema = QuoteSelectorSchema()
        data = {"text": "process, system,|method of operation|, concept, principle"}
        result = schema.load(data)
        assert result.exact.startswith("method")


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

