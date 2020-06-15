from legislice.schemas import EnactmentSchema


class TestLoadEnactment:
    def test_load_nested_enactment(self, section6d):
        schema = EnactmentSchema()
        result = schema.load(section6d)
        assert result.heading.startswith("Waiver")

    def test_enactment_with_nested_selectors(self, section_11_subdivided):
        schema = EnactmentSchema()
        section_11_subdivided["quote_selection"] = [{}]
        section_11_subdivided["children"][1]["quote_selection"] = [
            {"exact": "hairdressers"}
        ]
        result = schema.load(section_11_subdivided)
        assert (
            result.selected_text()
            == "The Department of Beards may issue licenses to such...hairdressers"
        )
