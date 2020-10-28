from copy import deepcopy
from datetime import datetime
from legislice.mock_clients import JSONRepository, MOCK_USC_CLIENT
import os

from anchorpoint.textselectors import TextPositionSelector
from dotenv import load_dotenv
from marshmallow import ValidationError
import pytest

from legislice.download import Client
from legislice.name_index import collect_enactments
from legislice.schemas import (
    CrossReferenceSchema,
    EnactmentSchema,
    LinkedEnactmentSchema,
    SelectorSchema,
    enactment_needs_api_update,
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


class TestLoadCrossReference:
    client = Client(api_token=TOKEN, api_root=API_ROOT)

    def test_load_citation(self, citation_to_6c):
        schema = CrossReferenceSchema()
        result = schema.load(citation_to_6c)
        assert result.target_uri == "/test/acts/47/6C"


class TestLoadEnactment:
    client = Client(api_token=TOKEN, api_root=API_ROOT)

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
        answer = "The Department of Beards may issue licenses to such…hairdressers…"
        assert result.selected_text() == answer

    def test_enactment_with_True_as_selector(self, section_11_subdivided):
        schema = EnactmentSchema()
        section_11_subdivided["selection"] = True
        section_11_subdivided["children"][1]["selection"] = [{"start": 0, "end": 12}]
        result = schema.load(section_11_subdivided)
        answer = "The Department of Beards may issue licenses to such…hairdressers…"
        assert result.selected_text() == answer

    def test_enactment_with_False_as_selector(self, section_11_subdivided):
        schema = EnactmentSchema()
        section_11_subdivided["selection"] = False
        section_11_subdivided["children"][1]["selection"] = [{"start": 0, "end": 12}]
        result = schema.load(section_11_subdivided)
        answer = "…hairdressers…"
        assert result.selected_text() == answer

    def test_selector_not_wrapped_in_list(self, section_11_together):
        schema = EnactmentSchema()
        section_11_together["selection"] = {"start": 4, "end": 24}
        result = schema.load(section_11_together)
        assert result.selected_text() == "…Department of Beards…"

    def test_load_with_text_quote_selector(self, section_11_together):
        schema = EnactmentSchema()
        section_11_together["selection"] = [{"exact": "Department of Beards"}]
        result = schema.load(section_11_together)
        assert result.selected_text() == "…Department of Beards…"

    @pytest.mark.vcr()
    def test_load_enactment_with_text_anchor(self, provision_with_text_anchor):
        schema = EnactmentSchema()
        record = self.client.update_enactment_from_api(provision_with_text_anchor)
        result = schema.load(record)
        assert result.anchors[0].exact == "17 U.S.C. § 102(a)"

    def test_retrieve_enactment_by_name(self, section6d, section_11_together):
        obj, indexed = collect_enactments([section6d, section_11_together])
        schema = EnactmentSchema(many=True)
        schema.context["enactment_index"] = indexed
        enactments = schema.load(obj)
        assert enactments[0].start_date.isoformat() == "1935-04-01"

    def test_enactment_does_not_fail_for_excess_selector(self, section_11_subdivided):
        """Test selector that extends into the text of a subnode."""
        exact = "The Department of Beards may issue licenses to such barbers"
        section_11_subdivided["exact"] = exact
        schema = EnactmentSchema(many=False)
        enactment = schema.load(section_11_subdivided)

        assert enactment.selected_text() == exact + "…"

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

    def test_nest_selector_fields_before_loading(self):
        client = MOCK_USC_CLIENT
        raw_enactment = client.fetch(path="/us/const/amendment/IV", date="1791-12-15")
        raw_enactment["selection"] = [{"start": 10, "end": 20}]
        raw_enactment["suffix"] = ", and no Warrants shall issue"
        schema = EnactmentSchema()
        updated = schema.move_selector_fields(raw_enactment)
        assert updated["selection"][1]["suffix"] == ", and no Warrants shall issue"

    def test_load_enactment_with_cross_reference(self):
        data = {
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


class TestDumpEnactment:

    client = Client(api_token=TOKEN, api_root=API_ROOT)

    @pytest.mark.vcr()
    def test_dump_enactment_with_selector_to_dict(self):
        copyright_clause = self.client.read("/us/const/article/I/8/8")
        copyright_clause.select("Science and useful Arts")

        schema = EnactmentSchema()
        dumped = schema.dump(copyright_clause)
        selection = dumped["selection"][0]
        quote = dumped["content"][selection["start"] : selection["end"]]
        assert quote == "Science and useful Arts"
