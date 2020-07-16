from datetime import date
import os

from anchorpoint import TextQuoteSelector, TextPositionSelector
from anchorpoint.textselectors import TextPositionSet
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

    def test_protect_from_change(self):
        subsection = Enactment(
            heading="",
            content="The beardcoin shall be a cryptocurrency token.",
            node="/test/acts/47/6C/1",
            start_date=date(2013, 7, 18),
        )
        with pytest.raises(AttributeError):
            subsection.content = "The beardcoin shall be a gold coin."

    def test_create_TextPositionSet_on_init(self, section_11_subdivided):
        schema = EnactmentSchema()
        section_11_subdivided["selection"] = [{"start": 0}]
        for child in section_11_subdivided["children"]:
            child["selection"] = []
        section_11_subdivided["children"][1]["selection"] = [{"start": 0, "end": 12}]
        result = schema.load(section_11_subdivided)
        assert isinstance(result.selection, TextPositionSet)
        assert (
            result.selected_text()
            == "The Department of Beards may issue licenses to such...hairdressers..."
        )


class TestEnactmentDetails:
    @pytest.mark.vcr()
    def test_usc_enactment_is_statute(self):
        client = Client(api_token=TOKEN)
        enactment = client.read(path="/us/usc/t17/s103", date="2020-01-01")
        assert enactment.sovereign == "us"
        assert enactment.level == "statute"

    @pytest.mark.vcr()
    def test_str_representation(self):
        client = Client(api_token=TOKEN)
        enactment = client.read(path="/us/const/amendment/IV")
        selection = TextQuoteSelector(
            exact="The right of the people to be secure in their persons"
        )
        enactment.select(selection)
        assert enactment.level == "constitution"
        assert "secure in their persons..." in str(enactment)
        assert enactment.node in str(enactment)
        assert "1791-12-15" in str(enactment)

    def test_code_representation(self):
        client = Client(api_token=TOKEN)
        enactment = client.read(path="/us/const")


class TestSelectText:
    client = Client(api_token=TOKEN)

    @pytest.mark.vcr()
    def test_get_all_text(self):
        section = self.client.read(path="/test/acts/47/11")
        assert "barbers, hairdressers, or other" in section.text

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

    def test_text_sequence_selected_with_bool(self):
        section = Enactment(
            heading="Issuance of beardcoin",
            content="Where an exemption is granted...",
            node="/test/acts/47/6C",
            children=[],
            end_date=None,
            start_date=date(1935, 4, 1),
        )
        assert section.text_sequence()[0].text == "Where an exemption is granted..."

    @pytest.mark.vcr()
    def test_str_for_text_sequence(self):
        section = self.client.read(path="/test/acts/47/11")
        quotes = [
            TextQuoteSelector(
                exact="The Department of Beards may issue licenses to such"
            ),
            TextQuoteSelector(exact="hairdressers", suffix=", or other male grooming"),
            TextQuoteSelector(exact="as they see fit"),
        ]
        section.select(quotes)
        text_sequence = section.text_sequence()
        assert str(text_sequence) == (
            "The Department of Beards may issue "
            "licenses to such...hairdressers...as they see fit..."
        )


class TestSelectFromEnactment:
    client = Client(api_token=TOKEN)

    def test_text_of_enactment_subset(self, section_11_together):
        schema = EnactmentSchema()
        combined = schema.load(section_11_together)
        selector = TextQuoteSelector(
            exact="barbers, hairdressers, or other male grooming professionals"
        )
        combined.select(selector)
        sequence = combined.text_sequence()
        assert str(sequence).strip(".").startswith("barbers")

    @pytest.mark.vcr()
    def test_select_nested_text_with_positions(self):
        phrases = TextPositionSet(
            TextPositionSelector(0, 51),
            TextPositionSelector(61, 73),
            TextPositionSelector(112, 127),
        )
        section = self.client.read(path="/test/acts/47/11")
        section.select(phrases)
        text_sequence = section.text_sequence()
        assert str(text_sequence) == (
            "The Department of Beards may issue licenses to "
            "such...hairdressers...as they see fit..."
        )

    def test_select_none(self, section_11_subdivided):
        schema = EnactmentSchema()
        combined = schema.load(section_11_subdivided)
        combined.select(False)
        assert combined.selected_text() == "..."

    def test_select_none_with_None(self, section_11_subdivided):
        schema = EnactmentSchema()
        combined = schema.load(section_11_subdivided)
        combined.select(None)
        assert combined.selected_text() == "..."

    def test_select_all(self, section_11_subdivided):
        """Clear selected text, and then select one subsection."""
        schema = EnactmentSchema()
        combined = schema.load(section_11_subdivided)
        combined.select(None)
        combined.children[3].select()
        assert (
            combined.selected_text()
            == "...as they see fit to purchase a beardcoin from a customer..."
        )
        assert (
            combined.children[3].selected_text()
            == "as they see fit to purchase a beardcoin from a customer"
        )

    def test_select_all_nested(self, section_11_subdivided):
        """Clear selected text, and then select one subsection."""
        schema = EnactmentSchema()
        combined = schema.load(section_11_subdivided)
        combined.select()
        assert combined.selected_text().startswith("The Department of Beards")

    def test_error_for_unusable_selector(self, section_11_subdivided):
        schema = EnactmentSchema()
        combined = schema.load(section_11_subdivided)
        selection = TextPositionSet(
            TextPositionSelector(0, 10), TextPositionSelector(1000, 1010)
        )
        with pytest.raises(ValueError):
            combined.children[3].select(selection)

    @pytest.mark.vcr()
    def test_get_positions_from_quotes(self):
        section = self.client.read(path="/test/acts/47/11")
        quotes = [
            TextQuoteSelector(
                exact="The Department of Beards may issue licenses to such"
            ),
            TextQuoteSelector(exact="hairdressers", suffix=", or other male grooming"),
            TextQuoteSelector(exact="as they see fit"),
        ]
        positions = section.get_positions_for_quotes(quotes)
        assert positions == TextPositionSet(
            TextPositionSelector(0, 51),
            TextPositionSelector(61, 73),
            TextPositionSelector(112, 127),
        )

    @pytest.mark.vcr()
    def test_text_sequence_has_no_consecutive_Nones(self):
        amend_14 = self.client.read(path="/us/const/amendment/XIV")
        selector = TextQuoteSelector(exact="life, liberty, or property")
        amend_14.select(selector)
        selected_list = amend_14.text_sequence()

        assert len(selected_list) == 3
        assert selected_list[0] is None
        assert selected_list[1].text == "life, liberty, or property"
        assert selected_list[2] is None

    def test_select_with_position_selector(self, section_11_together):
        schema = EnactmentSchema()
        section = schema.load(section_11_together)
        section.select(TextPositionSelector(start=29, end=43))
        assert section.selected_text() == "...issue licenses..."


class TestCompareEnactment:
    client = Client(api_token=TOKEN)

    @pytest.mark.vcr()
    def test_equal_enactment_text(self):
        """Test provisions with the same text (different dates)."""
        old_version = self.client.read(path="/test/acts/47/6A", date=date(1999, 1, 1))
        new_version = self.client.read(path="/test/acts/47/6A", date=date(2020, 1, 1))
        assert old_version.means(new_version)

    @pytest.mark.vcr()
    def test_not_gt_if_equal(self):
        enactment = self.client.read(path="/test/acts/47/1", date=date(1999, 1, 1))
        assert enactment == enactment
        assert not enactment > enactment
        assert enactment >= enactment

    @pytest.mark.vcr()
    def test_different_section_same_text(self):
        old_version = self.client.read("/test/acts/47/8/2/b", date=date(1999, 1, 1))
        new_version = self.client.read("/test/acts/47/8/2/d", date=date(2020, 1, 1))
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
            path="/test/acts/47/8/2", date=date(2020, 1, 1)
        )
        fewer_provisions = self.client.read(
            path="/test/acts/47/8/2", date=date(1999, 1, 1)
        )
        assert more_provisions >= fewer_provisions
        assert more_provisions > fewer_provisions

    @pytest.mark.vcr()
    def test_fewer_provisions_does_not_imply_more(self):
        more_provisions = self.client.read(
            path="/test/acts/47/8/2", date=date(2020, 1, 1)
        )
        fewer_provisions = self.client.read(
            path="/test/acts/47/8/2", date=date(1999, 1, 1)
        )
        assert not fewer_provisions >= more_provisions
        assert not fewer_provisions > more_provisions

    def test_enactment_subset(self, section_11_together):
        schema = EnactmentSchema()
        combined = schema.load(section_11_together)
        limited = schema.load(section_11_together)
        selector = TextQuoteSelector(
            exact="barbers, hairdressers, or other male grooming professionals"
        )
        limited.select(selector)
        assert not combined.means(limited)
        assert combined > limited

    @pytest.mark.vcr()
    def test_same_phrase_different_provisions(self):
        amend_5 = self.client.read(path="/us/const/amendment/V")
        amend_14 = self.client.read(path="/us/const/amendment/XIV/1")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        amend_5.select(selector)
        amend_14.select(selector)
        assert amend_5.means(amend_14)

    @pytest.mark.vcr()
    def test_same_phrase_selected_in_nested_provision(self):
        amend_5 = self.client.read(path="/us/const/amendment/V")
        amend_14 = self.client.read(path="/us/const/amendment/XIV")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        amend_5.select(selector)
        amend_14.select(selector)
        assert amend_5.means(amend_14)

    def test_enactment_does_not_imply_textsequence(self, section_11_subdivided):
        schema = EnactmentSchema()
        subdivided = schema.load(section_11_subdivided)
        text = subdivided.text_sequence()
        assert not subdivided > text
