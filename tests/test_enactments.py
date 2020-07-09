from datetime import date
import os

from anchorpoint import TextQuoteSelector
from dotenv import load_dotenv
import pytest

from legislice.download import Client
from legislice.enactments import Enactment
from legislice.schemas import EnactmentSchema

load_dotenv()

TOKEN = os.getenv("LEGISLICE_API_TOKEN")


class TestMakeEnactment:
    def test_init_enactment_without_nesting(self):
        s1 = Enactment(
            node="/test/acts/47/1",
            start_date=date(1935, 4, 1),
            heading="Short title",
            content=(
                "This Act may be cited as the Australian Beard Tax"
                " (Promotion of Enlightenment Values) Act 1934."
            ),
        )
        assert s1.end_date is None

    def test_init_enactment_with_nesting(self):
        subsection = Enactment(
            heading="",
            content="The beardcoin shall be a cryptocurrency token...",
            node="/test/acts/47/6C/1",
            start_date=date(2013, 7, 18),
        )

        section = Enactment(
            heading="Issuance of beardcoin",
            content="Where an exemption is granted under section 6...",
            node="/test/acts/47/6C",
            children=[subsection],
            end_date=None,
            start_date=date(1935, 4, 1),
        )

        assert section.children[0].content.startswith("The beardcoin shall")


class TestSelectText:
    def test_select_text_with_bool(self):
        subsection = Enactment(
            heading="",
            content="The beardcoin shall be a cryptocurrency token...",
            node="/test/acts/47/6C/1",
            start_date=date(2013, 7, 18),
            selection=False,
        )

        section = Enactment(
            heading="Issuance of beardcoin",
            content="Where an exemption is granted...",
            node="/test/acts/47/6C",
            children=[subsection],
            end_date=None,
            start_date=date(1935, 4, 1),
        )
        assert section.selected_text == "Where an exemption is granted..."
        assert "cryptocurrency" not in section.selected_text

    def test_selected_as_list_selected_with_bool(self):
        section = Enactment(
            heading="Issuance of beardcoin",
            content="Where an exemption is granted...",
            node="/test/acts/47/6C",
            children=[],
            end_date=None,
            start_date=date(1935, 4, 1),
        )
        assert section.selected_as_list()[0].text == "Where an exemption is granted..."


class TestSelectFromEnactment:
    def test_text_of_enactment_subset(self, section_11_together):
        schema = EnactmentSchema()
        combined = schema.load(section_11_together)
        selector = TextQuoteSelector(
            exact="barbers, hairdressers, or other male grooming professionals"
        )
        limited = combined.use_selector(selector)
        assert limited.selected_text.startswith("barbers")


class TestCompareEnactment:
    client = Client(api_token=TOKEN)

    @pytest.mark.vcr()
    def test_equal_enactment_text(self):
        """Test provisions with the same text (different dates)."""
        old_version = self.client.read(uri="/test/acts/47/6A", date=date(1999, 1, 1))
        new_version = self.client.read(uri="/test/acts/47/6A", date=date(2020, 1, 1))
        assert old_version.means(new_version)

    @pytest.mark.vcr()
    def test_not_gt_if_equal(self):
        enactment = self.client.read(uri="/test/acts/47/1", date=date(1999, 1, 1))
        assert enactment == enactment
        assert not enactment > enactment
        assert enactment >= enactment

    @pytest.mark.vcr()
    def test_different_section_same_text(self):
        old_version = self.client.read(uri="/test/acts/47/8/2/b", date=date(1999, 1, 1))
        new_version = self.client.read(uri="/test/acts/47/8/2/d", date=date(2020, 1, 1))
        assert old_version.means(new_version)

    @pytest.mark.vcr()
    def test_combined_section_implies_subdivided_section(
        self, section_11_together, section_11_subdivided
    ):
        schema = EnactmentSchema()
        combined = schema.load(section_11_together)
        subdivided = schema.load(section_11_subdivided)
        assert combined >= subdivided
        assert combined > subdivided

    @pytest.mark.vcr()
    def test_more_provisions_implies_fewer(self):
        more_provisions = self.client.read(
            uri="/test/acts/47/8/2", date=date(2020, 1, 1)
        )
        fewer_provisions = self.client.read(
            uri="/test/acts/47/8/2", date=date(1999, 1, 1)
        )
        assert more_provisions >= fewer_provisions
        assert more_provisions > fewer_provisions

    def test_enactment_subset(self, section_11_together):
        schema = EnactmentSchema()
        combined = schema.load(section_11_together)
        selector = TextQuoteSelector(
            exact="barbers, hairdressers, or other male grooming professionals"
        )
        limited = combined.use_selector(selector)
        assert combined > limited
