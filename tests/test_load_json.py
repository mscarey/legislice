import pytest

from legislice.download import JSONRepository


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
