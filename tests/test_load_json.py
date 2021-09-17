from datetime import date

from anchorpoint import TextQuoteSelector
import pytest
from legislice.download import Client


class TestUpdateEnactments:
    """
    Tests for filling in blank fields in JSON Enactments with the test Client.

    The Enactments that need filling in could be user-generated as part of a model
    of an AuthoritySpoke holding, and can have some fields missing.
    The Enactments that come from the Client can be assumed not to be missing fields.
    """

    @pytest.mark.vcr
    def test_update_entries_in_enactment_index(self, test_client):
        enactment_index = {
            "security": {
                "enactment": {
                    "node": "/us/const/amendment/IV",
                    "start_date": "1791-12-15",
                },
                "selection": {
                    "quotes": [{"exact": "right of the people to be secure"}]
                },
            }
        }
        client = test_client
        updated_index = client.update_entries_in_enactment_index(enactment_index)
        updated_enactment = updated_index["security"]
        assert updated_enactment["enactment"]["heading"] == "AMENDMENT IV."
        assert updated_enactment["enactment"]["url"].startswith("https")

    @pytest.mark.vcr
    def test_update_entry_without_date(self, test_client):
        enactment_index = {
            "person clause": {
                "enactment": {"node": "/us/const/amendment/XIV/3"},
                "selection": {
                    "positions": [{"start": 3, "end": 15}],
                },
            }
        }
        client = test_client
        updated_index = client.update_entries_in_enactment_index(enactment_index)
        updated_passage = updated_index["person clause"]
        assert updated_passage["enactment"]["heading"].startswith(
            "Loyalty as a qualification"
        )
        loaded_enactment = client.read_passage_from_json(updated_passage)
        assert loaded_enactment.selected_text() == "…person shall…"

    @pytest.mark.vcr
    def test_read_enactment_with_suffix_field(self, test_client):
        raw_enactment = {
            "enactment": {
                "name": "search clause",
                "node": "/us/const/amendment/IV",
                "start_date": "1791-12-15",
            },
            "selection": {
                "quotes": {
                    "suffix": ", and no Warrants shall issue",
                }
            },
        }

        passage = test_client.read_passage_from_json(raw_enactment)
        assert passage.selected_text().endswith("shall not be violated…")

    @pytest.mark.vcr()
    def test_update_linked_enactment(self, test_client):
        data = {"node": "/us/const"}
        new = test_client.update_enactment_from_api(data)
        assert new["node"] == "/us/const"
        assert new["start_date"] == "1788-09-13"
        assert isinstance(new["children"][0], str)

    @pytest.mark.vcr()
    def test_update_enactment_when_reading_from_json(self, test_client):
        enactment = test_client.read_from_json(data={"node": "/us/const/amendment/IV"})
        assert enactment.start_date.isoformat() == "1791-12-15"

    @pytest.mark.vcr()
    def test_text_in_updated_enactment_is_selected_by_default(self, test_client):
        client = test_client
        passage = client.read_passage_from_json(
            data={"enactment": {"node": "/us/const/amendment/IV"}}
        )
        assert passage.selected_text().startswith("The right")


class TestLoadAndSelect:
    client = Client()
    client.coverage["/us/usc"] = {
        "earliest_in_db": date(1750, 1, 1),
        "first_published": date(1750, 1, 1),
    }
    response = {
        "heading": "",
        "start_date": "2013-07-18",
        "node": "/us/usc/t18/s1960/b/1",
        "text_version": {
            "id": 943740,
            "url": "https://authorityspoke.com/api/v1/textversions/943740/",
            "content": "the term “unlicensed money transmitting business” means a money transmitting business which affects interstate or foreign commerce in any manner or degree and—",
        },
        "url": "https://authorityspoke.com/api/v1/us/usc/t18/s1960/b/1/",
        "end_date": None,
        "children": [
            {
                "heading": "",
                "start_date": "2013-07-18",
                "node": "/us/usc/t18/s1960/b/1/A",
                "text_version": {
                    "id": 943737,
                    "url": "https://authorityspoke.com/api/v1/textversions/943737/",
                    "content": "is operated without an appropriate money transmitting license in a State where such operation is punishable as a misdemeanor or a felony under State law, whether or not the defendant knew that the operation was required to be licensed or that the operation was so punishable;",
                },
                "url": "https://authorityspoke.com/api/v1/us/usc/t18/s1960/b/1/A/",
                "end_date": None,
                "children": [],
                "citations": [],
            },
            {
                "heading": "",
                "start_date": "2013-07-18",
                "node": "/us/usc/t18/s1960/b/1/B",
                "text_version": {
                    "id": 943738,
                    "url": "https://authorityspoke.com/api/v1/textversions/943738/",
                    "content": "fails to comply with the money transmitting business registration requirements under section 5330 of title 31, United States Code, or regulations prescribed under such section; or",
                },
                "url": "https://authorityspoke.com/api/v1/us/usc/t18/s1960/b/1/B/",
                "end_date": None,
                "children": [],
                "citations": [],
            },
            {
                "heading": "",
                "start_date": "2013-07-18",
                "node": "/us/usc/t18/s1960/b/1/C",
                "text_version": {
                    "id": 943739,
                    "url": "https://authorityspoke.com/api/v1/textversions/943739/",
                    "content": "otherwise involves the transportation or transmission of funds that are known to the defendant to have been derived from a criminal offense or are intended to be used to promote or support unlawful activity;",
                },
                "url": "https://authorityspoke.com/api/v1/us/usc/t18/s1960/b/1/C/",
                "end_date": None,
                "children": [],
                "citations": [],
            },
        ],
        "citations": [],
        "parent": "https://authorityspoke.com/api/v1/us/usc/t18/s1960/b/",
    }

    def test_select_text_with_end_param(self):
        law = self.client.read_from_json(self.response)
        passage = law.select(
            TextQuoteSelector(suffix=", whether or not the defendant knew")
        )
        assert passage.selected_text().endswith("or a felony under State law…")

    def test_end_param_has_no_effect_when_nothing_selected(self):
        law = self.client.read_from_json(self.response)
        passage = law.select(selection=False, end="or a felony under State law")
        assert passage.selected_text() == ""
