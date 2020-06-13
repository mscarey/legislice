import datetime
import os

from dotenv import load_dotenv
import pytest

from legislice.download import Client

load_dotenv()

TOKEN = os.getenv("LEGISLICE_API_TOKEN")


class TestDownloadJSON:
    @pytest.mark.vcr()
    def test_fetch_section(self):
        client = Client(api_token=TOKEN)
        s102 = client.fetch(uri="/test/acts/47/1")
        assert s102["start_date"] == "1935-04-01"
        assert s102["end_date"] is None
        assert s102["heading"] == "Short title"

    @pytest.mark.vcr()
    def test_extraneous_word_token_before_api_token(self):
        extraneous_word_token = "Token " + TOKEN
        client = Client(api_token=extraneous_word_token)
        s102 = client.fetch(uri="/test/acts/47/1")
        assert s102["start_date"] == "1935-04-01"
        assert s102["end_date"] is None
        assert s102["heading"] == "Short title"

    @pytest.mark.vcr()
    def test_fetch_current_section_with_date(self):
        client = Client(api_token=TOKEN)
        waiver = client.fetch(uri="/test/acts/47/6D", date=datetime.date(2020, 1, 1))
        assert waiver["url"].endswith("acts/47/6D@2020-01-01")
        assert waiver["children"][0]["start_date"] == "2013-07-18"

    @pytest.mark.vcr()
    def test_fetch_past_section_with_date(self):
        client = Client(api_token=TOKEN)
        waiver = client.fetch(uri="/test/acts/47/6D", date=datetime.date(1940, 1, 1))
        assert waiver["url"].endswith("acts/47/6D@1940-01-01")
        assert waiver["children"][0]["start_date"] == "1935-04-01"
