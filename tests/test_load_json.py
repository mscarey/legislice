import pytest


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
                "node": "/us/const/amendment/IV",
                "start_date": "1791-12-15",
                "exact": "right of the people to be secure",
            }
        }
        client = test_client
        updated_index = client.update_entries_in_enactment_index(enactment_index)
        updated_enactment = updated_index["security"]
        assert updated_enactment["heading"] == "AMENDMENT IV."
        assert updated_enactment["url"].startswith("https")

    @pytest.mark.vcr
    def test_update_entry_without_date(self, test_client):
        enactment_index = {
            "person clause": {
                "node": "/us/const/amendment/XIV/3",
                "start": 3,
                "end": 15,
            }
        }
        client = test_client
        updated_index = client.update_entries_in_enactment_index(enactment_index)
        updated_enactment = updated_index["person clause"]
        assert updated_enactment["heading"].startswith("Loyalty as a qualification")
        loaded_enactment = client.read_from_json(updated_enactment)
        assert loaded_enactment.selected_text() == "…person shall…"

    @pytest.mark.vcr
    def test_read_enactment_with_suffix_field(self, test_client):
        raw_enactment = {
            "name": "search clause",
            "node": "/us/const/amendment/IV",
            "suffix": ", and no Warrants shall issue",
            "start_date": "1791-12-15",
        }
        enactment = test_client.read_from_json(raw_enactment)
        assert enactment.selected_text().endswith("shall not be violated…")

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
        enactment = client.read_from_json(data={"node": "/us/const/amendment/IV"})
        assert enactment.selected_text().startswith("The right")
