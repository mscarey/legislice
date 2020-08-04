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
