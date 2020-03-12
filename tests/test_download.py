import datetime

from legislice import client

ENDPOINT = "http://127.0.0.1:8000/api/v1"


class TestDownloadJSON:
    def test_fetch_section(self):
        s102 = client.fetch(uri="/test/acts/47/1", endpoint=ENDPOINT)
        assert s102["start_date"] == "1935-04-01"
        assert s102["end_date"] is None
        assert s102["heading"] == "Short title"

    def test_fetch_current_section_with_date(self):
        waiver = client.fetch(
            uri="/test/acts/47/6D", date=datetime.date(2020, 1, 1), endpoint=ENDPOINT
        )
        assert waiver["url"].endswith("acts/47/6D@2020-01-01")
        assert waiver["children"][0]["start_date"] == "2013-07-18"

    def test_fetch_past_section_with_date(self):
        waiver = client.fetch(
            uri="/test/acts/47/6D", date=datetime.date(1940, 1, 1), endpoint=ENDPOINT
        )
        assert waiver["url"].endswith("acts/47/6D@1940-01-01")
        assert waiver["children"][0]["start_date"] == "1935-04-01"

