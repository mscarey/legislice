import datetime
import os

from anchorpoint import TextQuoteSelector
from dotenv import load_dotenv
import pytest

from legislice.download import Client

load_dotenv()

TOKEN = os.getenv("LEGISLICE_API_TOKEN")


class TestDownloadJSON:
    @pytest.mark.vcr()
    def test_fetch_section(self):
        client = Client(api_token=TOKEN)
        s102 = client.fetch(path="/test/acts/47/1")
        assert s102["start_date"] == "1935-04-01"
        assert s102["end_date"] is None
        assert s102["heading"] == "Short title"

    @pytest.mark.vcr()
    def test_extraneous_word_token_before_api_token(self):
        extraneous_word_token = "Token " + TOKEN
        client = Client(api_token=extraneous_word_token)
        s102 = client.fetch(path="/test/acts/47/1")
        assert s102["start_date"] == "1935-04-01"
        assert s102["end_date"] is None
        assert s102["heading"] == "Short title"

    @pytest.mark.vcr()
    def test_fetch_current_section_with_date(self):
        client = Client(api_token=TOKEN)
        waiver = client.fetch(path="/test/acts/47/6D", date=datetime.date(2020, 1, 1))
        assert waiver["url"].endswith("acts/47/6D@2020-01-01")
        assert waiver["children"][0]["start_date"] == "2013-07-18"

    @pytest.mark.vcr()
    def test_fetch_past_section_with_date(self):
        client = Client(api_token=TOKEN)
        waiver = client.fetch(path="/test/acts/47/6D", date=datetime.date(1940, 1, 1))
        assert waiver["url"].endswith("acts/47/6D@1940-01-01")
        assert waiver["children"][0]["start_date"] == "1935-04-01"


class TestDownloadAndLoad:
    @pytest.mark.vcr()
    def test_make_enactment_from_selector_without_code(self):
        select = TextQuoteSelector(suffix=", shall be vested")
        client = Client(api_token=TOKEN)
        art_3 = client.read(path="/us/const/article/III/1", selector=select)

        assert art_3.selected_text.startswith("The judicial Power")
        assert art_3.selected_text.endswith("the United States...")

    @pytest.mark.vcr()
    def test_bad_uri_for_enactment(self):
        select = TextQuoteSelector(suffix=", shall be vested")
        client = Client(api_token=TOKEN)
        with pytest.raises(ValueError):
            art_3 = client.read(path="/us/const/article-III/1", selector=select)
