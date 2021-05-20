from copy import deepcopy
from datetime import datetime
import json

import os

from anchorpoint.textselectors import TextPositionSelector, TextQuoteSelector
from dotenv import load_dotenv
from marshmallow import ValidationError
import pytest

from legislice.download import Client

from legislice.schemas import (
    CrossReferenceSchema,
    EnactmentSchema,
    InboundReferenceSchema,
    LinkedEnactmentSchema,
    PositionSelectorSchema,
    CitingProvisionLocationSchema,
    enactment_needs_api_update,
)

from legislice.yaml_schemas import (
    SelectorSchema,
    ExpandableEnactmentSchema,
    get_schema_for_node,
)

load_dotenv()

TOKEN = os.getenv("LEGISLICE_API_TOKEN")
API_ROOT = os.getenv("API_ROOT")


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
        with pytest.raises(ValidationError):
            _ = schema.load(data)

    def test_get_linked_schema(self):
        schema = get_schema_for_node("/us/usc")
        assert schema.__name__ == "LinkedEnactmentSchema"

    def test_get_expandable_linked_schema(self):
        schema = get_schema_for_node("/us/usc", use_text_expansion=True)
        assert schema.__name__ == "ExpandableLinkedEnactmentSchema"


class TestLoadCrossReference:
    client = Client(api_token=TOKEN, api_root=API_ROOT)

    def test_load_citation(self, citation_to_6c):
        schema = CrossReferenceSchema()
        result = schema.load(citation_to_6c)
        assert result.target_uri == "/test/acts/47/6C"
        assert (
            str(result)
            == 'CrossReference(target_uri="/test/acts/47/6C", reference_text="Section 6C")'
        )


class TestLoadEnactment:
    client = Client(api_token=TOKEN, api_root=API_ROOT)

    def test_load_nested_enactment(self, section6d):
        schema = EnactmentSchema()
        result = schema.load(section6d)
        assert result.heading.startswith("Waiver")

    def test_enactment_with_nested_selectors(self, section_11_subdivided):
        schema = ExpandableEnactmentSchema()
        section_11_subdivided["selection"] = [{"start": 0}]
        for child in section_11_subdivided["children"]:
            child["selection"] = []
        section_11_subdivided["children"][1]["selection"] = [{"start": 0, "end": 12}]
        result = schema.load(section_11_subdivided)
        answer = "The Department of Beards may issue licenses to such…hairdressers…"
        assert result.selected_text() == answer

    def test_enactment_with_True_as_selector(self, section_11_subdivided):
        schema = ExpandableEnactmentSchema()
        section_11_subdivided["selection"] = True
        section_11_subdivided["children"][1]["selection"] = [{"start": 0, "end": 12}]
        result = schema.load(section_11_subdivided)
        answer = "The Department of Beards may issue licenses to such…hairdressers…"
        assert result.selected_text() == answer

    def test_enactment_with_False_as_selector(self, section_11_subdivided):
        schema = ExpandableEnactmentSchema()
        section_11_subdivided["selection"] = False
        section_11_subdivided["children"][1]["selection"] = [{"start": 0, "end": 12}]
        result = schema.load(section_11_subdivided)
        answer = "…hairdressers…"
        assert result.selected_text() == answer

    def test_selector_not_wrapped_in_list(self, section_11_together):
        schema = ExpandableEnactmentSchema()
        section_11_together["selection"] = {"start": 4, "end": 24}
        result = schema.load(section_11_together)
        assert result.selected_text() == "…Department of Beards…"

    def test_load_with_text_quote_selector(self, section_11_together):
        schema = ExpandableEnactmentSchema()
        section_11_together["selection"] = [{"exact": "Department of Beards"}]
        result = schema.load(section_11_together)
        assert result.selected_text() == "…Department of Beards…"

    @pytest.mark.vcr()
    def test_load_enactment_with_text_anchor(
        self, provision_with_text_anchor, test_client
    ):
        schema = ExpandableEnactmentSchema()
        record = test_client.update_enactment_from_api(provision_with_text_anchor)
        result = schema.load(record)
        assert result.anchors[0].exact == "17 U.S.C. § 102(a)"

    def test_enactment_does_not_fail_for_excess_selector(self, section_11_subdivided):
        """Test selector that extends into the text of a subnode."""
        exact = "The Department of Beards may issue licenses to such barbers"
        section_11_subdivided["exact"] = exact
        schema = ExpandableEnactmentSchema(many=False)
        enactment = schema.load(section_11_subdivided)

        assert enactment.selected_text() == exact + "…"

    def test_load_enactment_missing_textversion_field(self, fourth_a_no_text_version):
        schema = ExpandableEnactmentSchema(many=False)
        enactment = schema.load(fourth_a_no_text_version)
        assert enactment.text.startswith("The right of the people")

    def test_node_field_needed_to_load_enactment(self):
        barbers_without_node = {
            "heading": "",
            "content": "barbers,",
            "children": [],
            "end_date": None,
            "start_date": "2013-07-18",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/11/i@2020-01-01",
        }
        with pytest.raises(ValueError):
            _ = enactment_needs_api_update(barbers_without_node)

    def test_nest_selector_fields_before_loading(self, test_client, fourth_a):
        fourth_a["selection"] = [{"start": 10, "end": 20}]
        fourth_a["suffix"] = ", and no Warrants shall issue"
        schema = ExpandableEnactmentSchema()
        updated = schema.move_selector_fields(fourth_a)
        assert updated["selection"][1]["suffix"] == ", and no Warrants shall issue"

    def test_load_enactment_with_cross_reference(self):
        data = {
            "heading": "",
            "content": "The Department of Beards shall waive the collection of beard tax upon issuance of beardcoin under Section 6C where the reason the maintainer wears a beard is due to bona fide religious, cultural, or medical reasons.",
            "start_date": "2013-07-18",
            "node": "/test/acts/47/6D/1",
            "children": [],
            "end_date": None,
            "url": "http://127.0.0.1:8000/api/v1/test/acts/47/6D/1@2020-01-01/",
            "citations": [
                {
                    "target_uri": "/test/acts/47/6C",
                    "target_url": "http://127.0.0.1:8000/api/v1/test/acts/47/6C@2020-01-01/",
                    "target_node": 1660695,
                    "reference_text": "Section 6C",
                }
            ],
        }
        schema = EnactmentSchema(many=False)
        enactment = schema.load(data)
        assert len(enactment._cross_references) == 1

    def test_load_enactment_with_nested_cross_reference(self):
        data = {
            "heading": "Waiver of beard tax in special circumstances",
            "content": "",
            "start_date": "1935-04-01",
            "node": "/test/acts/47/6D",
            "children": [
                {
                    "heading": "",
                    "content": "The Department of Beards shall waive the collection of beard tax upon issuance of beardcoin under Section 6C where the reason the maintainer wears a beard is due to bona fide religious, cultural, or medical reasons.",
                    "start_date": "2013-07-18",
                    "node": "/test/acts/47/6D/1",
                    "children": [],
                    "end_date": None,
                    "url": "http://127.0.0.1:8000/api/v1/test/acts/47/6D/1@2020-01-01",
                    "citations": [
                        {
                            "target_uri": "/test/acts/47/6C",
                            "target_url": "http://127.0.0.1:8000/api/v1/test/acts/47/6C@2020-01-01",
                            "target_node": 1660695,
                            "reference_text": "Section 6C",
                        }
                    ],
                }
            ],
            "end_date": None,
            "url": "http://127.0.0.1:8000/api/v1/test/acts/47/6D@2020-01-01",
            "citations": [],
            "parent": "http://127.0.0.1:8000/api/v1/test/acts/47@2020-01-01",
        }
        schema = EnactmentSchema(many=False)
        enactment = schema.load(data)
        refs = enactment.children[0]._cross_references
        assert len(refs) == 1


class TestLoadLinkedEnactment:
    client = Client(api_token=TOKEN, api_root=API_ROOT)

    def test_load_linked_enactment(self):
        schema = LinkedEnactmentSchema()
        data = {
            "type": "Enactment",
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

    @pytest.mark.vcr
    def test_text_sequence_for_linked_enactment(self, test_client):
        schema = LinkedEnactmentSchema()
        enactment = test_client.read(query="/test", date="2020-01-01")
        assert "for documentation." in enactment.text_sequence()[0].text
        assert "for documentation." in enactment.selected_text()
        enactment.select("for documentation.")
        assert enactment.selected_text() == "…for documentation."
        dumped = schema.dump(enactment)
        loaded = schema.load(dumped)
        assert loaded.selected_text() == "…for documentation."


class TestDumpEnactment:
    @pytest.mark.vcr()
    def test_dump_enactment_with_selector_to_dict(self, test_client):
        copyright_clause = test_client.read("/us/const/article/I/8/8")
        copyright_clause.select("Science and useful Arts")

        schema = EnactmentSchema()
        dumped = schema.dump(copyright_clause)
        selection = dumped["selection"][0]
        quote = dumped["text_version"]["content"][selection["start"] : selection["end"]]
        assert quote == "Science and useful Arts"

    @pytest.mark.vcr()
    def test_serialize_enactment_after_adding(self, fourth_a):
        schema = ExpandableEnactmentSchema()
        search = schema.load(fourth_a)
        warrant = deepcopy(search)

        search.select(TextQuoteSelector(suffix=", and no Warrants"))
        warrant.select(
            TextQuoteSelector(
                exact="shall not be violated, and no Warrants shall issue,"
            )
        )
        combined_enactment = search + warrant

        # search.select_more_text_at_current_node(warrant.selection)

        dumped = schema.dump(combined_enactment)

        assert dumped["text_version"]["content"].startswith("The right")
        assert dumped["text_version"].get("uri") is None

    @pytest.mark.vcr()
    def test_fields_ordered_with_children_last(self, test_client):
        s103 = test_client.read(query="/us/usc/t17/s103", date="2020-01-01")
        schema = EnactmentSchema()
        dumped = schema.dump(s103)
        assert list(dumped["children"][0]["selection"][0].keys()) == ["start", "end"]
        as_json = json.dumps(dumped)
        # Start field comes before end field in selector
        assert '"selection": [{"start":' in as_json
        # "Children" field is last, since it's hard to read otherwise
        assert list(dumped.keys())[-1] == "children"


class TestLoadInboundReferences:
    def test_load_citing_location_without_heading(self):
        location = {
            "heading": "",
            "node": "/us/usc/t17/s109/b/4",
            "start_date": "2013-07-18",
        }
        schema = CitingProvisionLocationSchema()
        loaded = schema.load(location)
        assert loaded.heading == ""
        assert loaded.start_date.isoformat() == "2013-07-18"

    def test_load_inbound_reference(self):
        """
        Test assuming the real target of the citation is given at the outer level of the dict.

        Only the first citation should be used to get data for the loaded object. The other
        one is irrelevant.
        """
        data = {
            "target_uri": "/us/usc/t17/s501",
            "citations": [
                {
                    "reference_text": "section 501 of this title",
                    "target_node": 1252985,
                    "target_uri": "/us/usc/t17/s501",
                    "target_url": "http://127.0.0.1:8000/api/v1/us/usc/t17/s501/",
                },
                {
                    "reference_text": "section 2319 of title 18",
                    "target_node": 1151186,
                    "target_uri": "/us/usc/t18/s2319",
                    "target_url": "http://127.0.0.1:8000/api/v1/us/usc/t18/s2319/",
                },
            ],
            "content": "Any person who distr... title 18.",
            "locations": [
                {
                    "heading": "",
                    "node": "/us/usc/t17/s109/b/4",
                    "start_date": "2013-07-18",
                }
            ],
            "url": "http://127.0.0.1:8000/api/v1/textversions/1031604/",
        }
        schema = InboundReferenceSchema()
        loaded = schema.load(data)
        assert loaded.target_uri == "/us/usc/t17/s501"
        assert loaded.reference_text == "section 501 of this title"
