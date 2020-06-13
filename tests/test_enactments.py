from datetime import date
import os

from dotenv import load_dotenv
import pytest

from legislice.download import Client
from legislice.enactments import Enactment

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
        assert section.selected_text() == "Where an exemption is granted..."
        assert "cryptocurrency" not in section.selected_text()


class TestCompareEnactment:
    @pytest.mark.vcr()
    def test_equal_enactment_text(self):
        """Test provisions with the same text (different dates)."""
        client = Client(api_token=TOKEN)
        old_version = client.read(uri="/test/acts/47/6A", date=date(1999, 1, 1))
        new_version = client.read(uri="/test/acts/47/6A", date=date(2020, 1, 1))
        assert old_version.means(new_version)
