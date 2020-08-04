import pytest

from legislice.download import JSONRepository
from legislice.name_index import EnactmentIndex


class TestLoadJson:
    def test_load_exact_date(self, mock_responses):
        client = JSONRepository(responses=mock_responses)
        enactment = client.read(path="/us/const/amendment/V", date="1791-12-15")
        assert enactment.content.startswith("No person shall be held")

    def test_load_after_start_date(self, mock_responses):
        client = JSONRepository(responses=mock_responses)
        enactment = client.read(path="/us/const/amendment/IV", date="1801-12-15")
        assert enactment.content.startswith("The right of the people")

    def test_load_no_date_specified(self, mock_responses):
        client = JSONRepository(responses=mock_responses)
        enactment = client.read(path="/us/const/article/I/8/8")
        assert enactment.heading == "Patents and copyrights."

    def test_date_is_too_early(self, mock_responses):
        client = JSONRepository(responses=mock_responses)
        with pytest.raises(ValueError):
            client.read(path="/us/usc/t17/s102/a", date="2010-12-15")
        assert True

    def test_find_subnode_of_entry(self, mock_responses):
        client = JSONRepository(responses=mock_responses)
        enactment = client.read(path="/us/usc/t17/s102/a/2")
        assert enactment.content.startswith("musical works")


class TestUpdateEnactments:
    """
    Tests for filling in blank fields in JSON Enactments with the mock Client.

    The Enactments that need filling in could be user-generated as part of a model
    of an AuthoritySpoke holding, and can have some fields missing.
    The Enactments that come from the Client can be assumed not to be missing fields.
    """

    def test_update_entries_in_enactment_index(self, mock_responses):
        enactment_index = EnactmentIndex(
            {
                "security": {
                    "node": "/us/const/amendment/IV",
                    "start_date": "1791-12-15",
                    "exact": "right of the people to be secure",
                }
            }
        )
        client = JSONRepository(responses=mock_responses)
        updated_index = client.update_entries_in_enactment_index(enactment_index)
        updated_enactment = updated_index.get_by_name("security")
        assert updated_enactment["heading"] == "AMENDMENT IV."
        assert updated_enactment["url"].startswith("https")

    def test_update_entry_without_date(self, mock_responses):
        enactment_index = EnactmentIndex(
            {
                "person clause": {
                    "node": "/us/const/amendment/XIV/3",
                    "start": 3,
                    "end": 15,
                }
            }
        )
        client = JSONRepository(responses=mock_responses)
        updated_index = client.update_entries_in_enactment_index(enactment_index)
        updated_enactment = updated_index.get_by_name("person clause")
        assert updated_enactment["heading"].startswith("Loyalty as a qualification")
        loaded_enactment = client.read_from_json(updated_enactment)
        assert loaded_enactment.selected_text() == "...person shall..."

