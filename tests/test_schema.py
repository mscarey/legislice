from copy import deepcopy
import json


from legislice.enactments import Enactment, EnactmentPassage

import os

from anchorpoint.textselectors import (
    TextPositionSelector,
    TextQuoteSelector,
    TextSelectionError,
)
from dotenv import load_dotenv
import pytest

from legislice.enactments import AnchoredEnactmentPassage
from legislice.download import Client

from legislice.schemas import (
    CrossReferenceSchema,
    EnactmentSchema,
    InboundReferenceSchema,
    LinkedEnactmentSchema,
    EnactmentPassageSchema,
    CitingProvisionLocationSchema,
    enactment_needs_api_update,
)

from legislice.yaml_schemas import (
    ExpandableEnactmentSchema,
    get_schema_for_node,
)

load_dotenv()

TOKEN = os.getenv("LEGISLICE_API_TOKEN")


class TestLoadSelector:
    def test_get_linked_schema(self):
        schema = get_schema_for_node("/us/usc")
        assert schema.__name__ == "LinkedEnactmentSchema"

    def test_get_expandable_linked_schema(self):
        schema = get_schema_for_node("/us/usc", use_text_expansion=True)
        assert schema.__name__ == "ExpandableLinkedEnactmentSchema"


class TestLoadCrossReference:
    client = Client(api_token=TOKEN)

    def test_load_citation(self, citation_to_6c):
        schema = CrossReferenceSchema()
        result = schema.load(citation_to_6c)
        assert result.target_uri == "/test/acts/47/6C"
        assert (
            str(result)
            == 'CrossReference(target_uri="/test/acts/47/6C", reference_text="Section 6C")'
        )


class TestLoadEnactment:
    client = Client(api_token=TOKEN)

    def test_load_nested_enactment(self, section6d):
        result = Enactment(**section6d)
        assert result.heading.startswith("Waiver")

    def test_enactment_with_nested_selectors(self, section_11_subdivided):
        length = len(section_11_subdivided["text_version"]["content"])
        data = {
            "selection": {
                "positions": {"start": 0, "end": length},
                "quotes": {"exact": "hairdressers"},
            },
            "enactment": section_11_subdivided,
        }
        passage = EnactmentPassage(**data)

        answer = "The Department of Beards may issue licenses to such…hairdressers…"
        assert passage.selected_text() == answer

    def test_selector_not_wrapped_in_list(self, section_11_together):
        data = {
            "selection": {"positions": {"start": 4, "end": 24}},
            "enactment": section_11_together,
        }
        result = EnactmentPassage(**data)
        assert result.selected_text() == "…Department of Beards…"

    def test_load_with_text_quote_selector(self, section_11_together):
        data = {
            "selection": {"quotes": {"exact": "Department of Beards"}},
            "enactment": section_11_together,
        }
        result = EnactmentPassage(**data)
        assert result.selected_text() == "…Department of Beards…"

    @pytest.mark.vcr()
    def test_load_enactment_with_text_anchor(
        self, provision_with_text_anchor, test_client
    ):
        provision_with_text_anchor["passage"][
            "enactment"
        ] = test_client.update_enactment_from_api(
            provision_with_text_anchor["passage"]["enactment"]
        )
        result = AnchoredEnactmentPassage(**provision_with_text_anchor)
        assert result.anchors.quotes[0].exact == "17 U.S.C. § 102(a)"

    def test_enactment_does_not_fail_for_excess_selector(self, section_11_subdivided):
        """Test selector that extends into the text of a subnode."""
        exact = "The Department of Beards may issue licenses to such barbers"
        data = {
            "enactment": section_11_subdivided,
            "selection": {"quotes": {"exact": exact}},
        }
        passage = EnactmentPassage(**data)

        assert passage.selected_text() == exact + "…"

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
        enactment = Enactment(**data)
        assert len(enactment.cross_references()) == 1

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
        refs = enactment.children[0].cross_references()
        assert len(refs) == 1


class TestLoadLinkedEnactment:
    client = Client(api_token=TOKEN)

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
        enactment = test_client.read(query="/test", date="2020-01-01")
        assert "for documentation." in enactment.text_sequence()[0].text
        assert "for documentation." in enactment.text
        passage = enactment.select("for documentation.")
        assert passage.selected_text() == "…for documentation."
        dumped = passage.dict()
        loaded = EnactmentPassage(**dumped)
        assert loaded.selected_text() == "…for documentation."


class TestDumpEnactment:
    @pytest.mark.vcr()
    def test_dump_enactment_with_selector_to_dict(self, test_client):
        copyright_clause = test_client.read("/us/const/article/I/8/8")
        passage = copyright_clause.select("Science and useful Arts")

        dumped = passage.dict()
        selection = dumped["selection"]["positions"][0]
        assert selection["end"] - selection["start"] == len("Science and useful Arts")

    @pytest.mark.vcr()
    def test_serialize_enactment_after_adding(self, fourth_a):
        enactment = Enactment(**fourth_a)
        search = enactment.select(TextQuoteSelector(suffix=", and no Warrants"))
        warrant = enactment.select(
            TextQuoteSelector(
                exact="shall not be violated, and no Warrants shall issue,"
            )
        )

        combined_enactment = search + warrant

        dumped = combined_enactment.dict()

        assert dumped["enactment"]["text_version"]["content"].startswith("The right")
        assert dumped["enactment"]["text_version"].get("uri") is None

    @pytest.mark.vcr()
    def test_fields_ordered_with_children_last(self, test_client):
        s103 = test_client.read(query="/us/usc/t17/s103", date="2020-01-01")
        passage = s103.select_all()
        as_json = passage.json()
        assert '"positions": [{"start": 0' in as_json


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
