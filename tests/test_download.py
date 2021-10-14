import datetime
from legislice import download
from legislice.enactments import CitingProvisionLocation, CrossReference
import os

from anchorpoint import TextQuoteSelector
from dotenv import load_dotenv
import pytest

from legislice.download import (
    Client,
    LegislicePathError,
    LegisliceTokenError,
    enactment_needs_api_update,
)
from legislice.enactments import InboundReference


load_dotenv()

TOKEN = os.getenv("LEGISLICE_API_TOKEN")
API_ROOT = "https://authorityspoke.com/api/v1"


class TestDownloadJSON:
    client = Client(api_token=TOKEN, api_root=API_ROOT)

    @pytest.mark.vcr()
    def test_fetch_section(self, test_client):
        url = self.client.url_from_enactment_path("/test/acts/47/1")
        response = self.client._fetch_from_url(url=url)

        # Test that there was no redirect from the API
        assert not response.history

        section = response.json()
        assert section["start_date"] == "1935-04-01"
        assert section["end_date"] is None
        assert section["heading"] == "Short title"

    def test_download_from_wrong_domain_raises_error(self, test_client):
        url = self.client.url_from_enactment_path("/test/acts/47/1")
        wrong_url = url.replace("authorityspoke.com", "pythonforlaw.com")
        with pytest.raises(ValueError):
            self.client._fetch_from_url(url=wrong_url)

    @pytest.mark.vcr()
    def test_fetch_current_section_with_date(self, test_client):
        url = self.client.url_from_enactment_path(
            "/test/acts/47/6D", date=datetime.date(2020, 1, 1)
        )
        response = self.client._fetch_from_url(url=url)

        # Test that there was no redirect from the API
        assert not response.history

        waiver = response.json()
        assert waiver["url"].endswith("acts/47/6D@2020-01-01/")
        assert waiver["children"][0]["start_date"] == "2013-07-18"

    @pytest.mark.vcr()
    def test_wrong_api_token(self):
        bad_client = Client(api_token="wr0ngToken")
        with pytest.raises(LegisliceTokenError):
            bad_client.fetch(query="/test/acts/47/1")

    @pytest.mark.vcr()
    def test_no_api_token(self):
        bad_client = Client()
        with pytest.raises(LegisliceTokenError):
            bad_client.fetch(query="/test/acts/47/1")

    @pytest.mark.vcr()
    def test_extraneous_word_token_before_api_token(self):
        extraneous_word_token = "Token " + TOKEN
        client = Client(api_token=extraneous_word_token, api_root=API_ROOT)
        s102 = client.fetch(query="/test/acts/47/1")
        assert s102["start_date"] == "1935-04-01"
        assert s102["end_date"] is None
        assert s102["heading"] == "Short title"

    @pytest.mark.vcr()
    def test_fetch_past_section_with_date(self, test_client):
        waiver = test_client.fetch(
            query="/test/acts/47/6D", date=datetime.date(1940, 1, 1)
        )
        assert waiver["url"].endswith("acts/47/6D@1940-01-01/")
        assert waiver["children"][0]["start_date"] == "1935-04-01"

    @pytest.mark.vcr()
    def test_fetch_cross_reference_to_old_version(self, test_client):
        """Test that statute can be fetched with a post-enactment date it was in effect."""
        reference = CrossReference(
            target_uri="/test/acts/47/8",
            target_url="https://authorityspoke.com/api/v1/test/acts/47/8@1935-04-01/",
            reference_text="section 8",
        )
        enactment = test_client.fetch_cross_reference(
            query=reference, date=datetime.date(1950, 1, 1)
        )
        assert enactment["start_date"] == "1935-04-01"
        assert enactment["url"].endswith("@1950-01-01/")

    @pytest.mark.vcr()
    def test_omit_terminal_slash(self, test_client):
        statute = test_client.fetch(query="us/usc/t17/s102/b/")
        assert not statute["node"].endswith("/")

    @pytest.mark.vcr()
    def test_add_omitted_initial_slash(self, test_client):
        statute = test_client.fetch(query="us/usc/t17/s102/b/")
        assert statute["node"].startswith("/")


class TestDownloadAndLoad:
    def test_make_enactment_from_citation(self, test_client, fourth_a):
        """
        Test fields for loaded Enactment.

        known_revision_date should indicate whether the start_date is known to be
        the date that the provision was revised in the USC.
        """

        result = test_client.read_from_json(fourth_a)
        assert result.text.endswith("persons or things to be seized.")
        assert result.known_revision_date is True

    @pytest.mark.vcr()
    def test_make_enactment_from_selector_without_code(self, test_client):
        selection = TextQuoteSelector(suffix=", shall be vested")
        art_3 = test_client.read(query="/us/const/article/III/1")
        passage = art_3.select(selection)
        text = passage.selected_text()

        assert text.startswith("The judicial Power")
        assert text.endswith("the United States…")

    @pytest.mark.vcr()
    def test_bad_uri_for_enactment(self, test_client):
        with pytest.raises(LegislicePathError):
            _ = test_client.read(query="/us/const/article-III/1")

    @pytest.mark.vcr()
    def test_unavailable_path_within_partial_match(self, test_client):
        """
        Test when a key appears to be an ancestor of the desired path, but isn't.

        This jargon may be a leftover from testing the mocks.
        """
        client = test_client
        with pytest.raises(LegislicePathError):
            client.read(
                query="/us/const/amendment/XIV/2/b", date=datetime.date(2010, 12, 15)
            )

    @pytest.mark.vcr
    def test_date_is_too_early(self, test_client):
        client = test_client
        with pytest.raises(LegislicePathError):
            client.read(query="/us/usc/t17/s102/a", date=datetime.date(2010, 12, 15))

    @pytest.mark.vcr()
    def test_chapeau_and_subsections_from_uslm_code(self, test_client):
        """
        Test that the selected_text includes the text of subsections.

        known_revision_date is not available on the subsection as well as
        the section.
        """
        definition = test_client.read(query="/test/acts/47/4")
        sequence = definition.text_sequence()
        assert str(sequence.strip()).endswith("below the nose.")
        assert definition.known_revision_date is True
        assert definition.children[0].known_revision_date is False

    @pytest.mark.vcr()
    def test_unknown_revision_date(self, test_client):
        """
        Test notation that enactment went into effect before start of the available data range.

        This test may begin to fail if earlier statute versions are
        loaded to the API's database.
        """
        enactment = test_client.read(query="/us/usc/t17/s103")
        assert enactment.known_revision_date is False
        assert enactment.children[0].known_revision_date is False

    @pytest.mark.vcr()
    def test_download_from_cross_reference(self, test_client):
        ref = CrossReference(
            target_uri="/test/acts/47/6C",
            target_url=f"{API_ROOT}/test/acts/47/6C@2020-01-01/",
            target_node=1660695,
            reference_text="Section 6C",
        )
        cited = test_client.fetch(ref)
        assert cited["text_version"]["content"].startswith(
            "Where an exemption is granted"
        )


class TestReadJSON:
    @pytest.mark.vcr()
    def test_read_from_cross_reference(self, test_client):
        """Test reading old version of statute by passing date param."""
        ref = CrossReference(
            target_uri="/test/acts/47/6D",
            target_url=f"{API_ROOT}/test/acts/47/6D",
            reference_text="Section 6D",
        )
        cited = test_client.read(ref, date="1950-01-01")
        assert "bona fide religious or cultural reasons." in cited.text

    @pytest.mark.vcr()
    def test_read_enactment_without_version_url(self, test_client):
        data = {
            "start_date": "1935-04-01",
            "selection": [
                {
                    "start": 0,
                    "end": 250,
                }
            ],
            "text_version": {
                "content": (
                    "Where the Department provides an exemption from the prohibition "
                    "in section 5, except as defined in section 6D, the person to whom "
                    "such exemption is granted shall be liable to pay to the Department "
                    "of Beards such fee as may be levied under section 6B."
                ),
                "id": None,
                "url": None,
            },
            "heading": "Levy of beard tax",
            "anchors": [],
            "children": [],
            "node": "/test/acts/47/6A",
            "end_date": None,
        }
        result = test_client.read_from_json(data)
        assert result.content.startswith("Where")

    @pytest.mark.vcr
    def test_check_db_coverage_when_reading(self):
        """
        Test whether default client can check DB coverage.

        This test would not work if pre-2013 sections were added to the DB.
        This test would not work with the test client because it doesn't
        check for USC coverage.
        """

        serialized = {
            "heading": "No retroactive effect",
            "start_date": "2013-07-18",
            "node": "/us/usc/t17/s1332",
            "text_version": {
                "id": 1032460,
                "url": "https://authorityspoke.com/api/v1/textversions/1032460/",
                "content": "Protection under this chapter shall not be available for any design that has been made public under section 1310(b) before the effective date of this chapter.",
            },
            "url": "https://authorityspoke.com/api/v1/us/usc/t17/s1332/",
            "end_date": None,
            "children": [],
            "citations": [],
            "parent": "https://authorityspoke.com/api/v1/us/usc/t17/",
        }
        client = download.Client(api_token=TOKEN, api_root=API_ROOT)
        enactment = client.read_from_json(serialized)
        assert enactment.known_revision_date is False


class TestInboundCitations:
    client = Client(api_token=TOKEN, api_root=API_ROOT)

    @pytest.mark.vcr()
    def test_fetch_inbound_citations_to_node(self, test_client):
        infringement_statute = test_client.read(
            query="/us/usc/t17/s501",
        )
        inbound_refs = test_client.fetch_citations_to(infringement_statute)
        period_ref = inbound_refs[0]["locations"][0]
        assert period_ref.get("text_version", {}).get("content") is None

    @pytest.mark.vcr()
    def test_fetch_inbound_citations_in_multiple_locations(self, test_client):
        """
        Test InboundReference with multiple "locations".

        The string should be something like:
        InboundReference to /us/usc/t2/s1301, from (/us/usc/t2/s60c-5/a/2/A 2013-07-18) and 2 other locations

        But it's not clear which of the three locations will be chosen.
        """

        definitions = "/us/usc/t2/s1301"
        inbound_refs = test_client.citations_to(definitions)
        period_ref = inbound_refs[0]
        assert str(period_ref).endswith("and 2 other locations")

    @pytest.mark.vcr()
    def test_read_inbound_citations_to_node(self, test_client):
        infringement_statute = test_client.read(
            query="/us/usc/t17/s501",
        )
        inbound_refs = test_client.citations_to(infringement_statute)
        assert inbound_refs[0].content.startswith(
            "Any person who distributes a phonorecord"
        )
        assert inbound_refs[1].content.startswith(
            "The relevant provisions of paragraphs (2)"
        )
        period_ref = inbound_refs[0].locations[0]
        assert isinstance(period_ref, CitingProvisionLocation)
        assert period_ref.node == "/us/usc/t17/s109/b/4"
        assert period_ref.start_date.isoformat() == "2013-07-18"

    @pytest.mark.vcr()
    def test_download_inbound_citations_from_uri(self, test_client):
        inbound_refs = test_client.citations_to("/us/usc/t17/s501")
        assert inbound_refs[0].content.startswith(
            "Any person who distributes a phonorecord"
        )

    @pytest.mark.vcr()
    def test_download_enactment_from_inbound_citation(self, test_client):
        reference = InboundReference(
            content="Any person who distributes...",
            reference_text="section 501 of this title",
            target_uri="/us/usc/t17/s501",
            locations=[
                CitingProvisionLocation(
                    heading="",
                    node="/us/usc/t17/s109/b/4",
                    start_date=datetime.date(2013, 7, 18),
                )
            ],
        )
        cited = test_client.read(reference)
        assert cited.node == "/us/usc/t17/s109/b/4"
        assert cited.start_date == datetime.date(2013, 7, 18)
        assert repr(reference).startswith("InboundReference(content=")

    @pytest.mark.vcr()
    def test_download_enactment_from_citing_location(self, test_client):

        location = CitingProvisionLocation(
            heading="",
            node="/us/usc/t17/s109/b/4",
            start_date=datetime.date(2013, 7, 18),
        )
        enactment = test_client.read(location)
        assert enactment.content.startswith("Any person who distributes")

    @pytest.mark.vcr()
    def test_enactment_downloaded_from_citing_location_has_text(self):

        inbound_refs = self.client.citations_to("/us/usc/t17/s501")
        assert str(inbound_refs[0]).startswith("InboundReference to /us/usc/t17/s501")
        assert inbound_refs[0].content.startswith(
            "Any person who distributes a phonorecord"
        )
        citing_enactment = self.client.read(inbound_refs[0])
        assert citing_enactment.node == "/us/usc/t17/s109/b/4"
        assert citing_enactment.text.startswith(
            "Any person who distributes a phonorecord"
        )

    def test_node_field_needed_to_update_enactment(self):
        barbers_without_node = {
            "heading": "",
            "content": "barbers,",
            "children": [],
            "end_date": None,
            "start_date": "2013-07-18",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/11/i@2020-01-01",
        }
        with pytest.raises(ValueError):
            _ = enactment_needs_api_update(barbers_without_node)

    def test_enactment_needs_api_update_with_str(self):
        assert enactment_needs_api_update("/us/usc") is False
