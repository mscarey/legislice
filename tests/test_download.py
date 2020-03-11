from legislice import client

ENDPOINT = "http://127.0.0.1:8000/api/v1"


class TestDownloadJSON:
    def test_fetch_section(self):
        s102 = client.fetch(uri="/test/acts/47/1", endpoint=ENDPOINT)
        assert s102["start_date"] == "1935-04-01"
        assert s102["end_date"] is None
        assert s102["text_version"]["heading"] == "Short title"
