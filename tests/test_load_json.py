import datetime
import pytest

from legislice.download import LegisliceDateError, LegislicePathError
from legislice.name_index import EnactmentIndex
from legislice.mock_clients import MOCK_USC_CLIENT


class TestLoadJson:
    def test_load_exact_date(self):
        enactment = MOCK_USC_CLIENT.read(
            path="/us/const/amendment/V", date="1791-12-15"
        )
        assert enactment.content.startswith("No person shall be held")

    def test_load_after_start_date(self):
        client = MOCK_USC_CLIENT
        enactment = client.read(path="/us/const/amendment/IV", date="1801-12-15")
        assert enactment.content.startswith("The right of the people")

    def test_load_no_date_specified(self):
        client = MOCK_USC_CLIENT
        enactment = client.read(path="/us/const/article/I/8/8")
        assert enactment.heading == "Patents and copyrights."

    def test_date_is_too_early(self):
        client = MOCK_USC_CLIENT
        with pytest.raises(LegisliceDateError):
            client.read(path="/us/usc/t17/s102/a", date=datetime.date(2010, 12, 15))

    def test_unavailable_path(self):
        client = MOCK_USC_CLIENT
        with pytest.raises(LegislicePathError):
            client.read(path="/test/acts/intolerable", date=datetime.date(2010, 12, 15))

    def test_unavailable_path_within_partial_match(self):
        """Test when a key appears to be an ancestor of the desired path, but isn't."""
        client = MOCK_USC_CLIENT
        with pytest.raises(LegislicePathError):
            client.read(
                path="/us/const/amendment/XIV/2/b", date=datetime.date(2010, 12, 15)
            )

    def test_find_subnode_of_entry(self):
        client = MOCK_USC_CLIENT
        enactment = client.read(path="/us/usc/t17/s102/a/2")
        assert enactment.content.startswith("musical works")


class TestUpdateEnactments:
    """
    Tests for filling in blank fields in JSON Enactments with the mock Client.

    The Enactments that need filling in could be user-generated as part of a model
    of an AuthoritySpoke holding, and can have some fields missing.
    The Enactments that come from the Client can be assumed not to be missing fields.
    """

    def test_update_entries_in_enactment_index(self):
        enactment_index = EnactmentIndex(
            {
                "security": {
                    "node": "/us/const/amendment/IV",
                    "start_date": "1791-12-15",
                    "exact": "right of the people to be secure",
                }
            }
        )
        client = MOCK_USC_CLIENT
        updated_index = client.update_entries_in_enactment_index(enactment_index)
        updated_enactment = updated_index.get_by_name("security")
        assert updated_enactment["heading"] == "AMENDMENT IV."
        assert updated_enactment["url"].startswith("https")

    def test_update_entry_without_date(self):
        enactment_index = EnactmentIndex(
            {
                "person clause": {
                    "node": "/us/const/amendment/XIV/3",
                    "start": 3,
                    "end": 15,
                }
            }
        )
        client = MOCK_USC_CLIENT
        updated_index = client.update_entries_in_enactment_index(enactment_index)
        updated_enactment = updated_index.get_by_name("person clause")
        assert updated_enactment["heading"].startswith("Loyalty as a qualification")
        loaded_enactment = client.read_from_json(updated_enactment)
        assert loaded_enactment.selected_text() == "…person shall…"


class TestReadJSON:
    def test_read_enactment_with_suffix_field(self):
        raw_enactment = {
            "name": "search clause",
            "node": "/us/const/amendment/IV",
            "suffix": ", and no Warrants shall issue",
            "start_date": "1791-12-15",
        }
        client = MOCK_USC_CLIENT
        enactment = client.read_from_json(raw_enactment)
        assert enactment.selected_text().endswith("shall not be violated…")
