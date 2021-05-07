from datetime import date
import os

from anchorpoint import TextQuoteSelector, TextPositionSelector
from anchorpoint.textselectors import TextPositionSet, TextSelectionError
from dotenv import load_dotenv
import pytest

from legislice.download import Client
from legislice.enactments import (
    CitingProvisionLocation,
    Enactment,
    InboundReference,
    LinkedEnactment,
    TextVersion,
    consolidate_enactments,
)
from legislice.schemas import EnactmentSchema
from legislice.yaml_schemas import ExpandableEnactmentSchema

load_dotenv()

TOKEN = os.getenv("LEGISLICE_API_TOKEN")
API_ROOT = os.getenv("API_ROOT")


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
        assert 'Enactment(node="/test/acts/47/1"' in repr(s1)

    def test_init_enactment_with_nesting(self):
        subsection = Enactment(
            heading="",
            content="The beardcoin shall be a cryptocurrency token…",
            node="/test/acts/47/6C/1",
            start_date=date(2013, 7, 18),
        )

        section = Enactment(
            heading="Issuance of beardcoin",
            content="Where an exemption is granted under section 6…",
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
            == "The Department of Beards may issue licenses to such…hairdressers…"
        )


class TestLinkedEnactment:
    client = Client(api_token=TOKEN, api_root=API_ROOT)

    @pytest.mark.vcr
    def test_text_sequence_for_linked_enactment(self, test_client):
        enactment = test_client.read(query="/test", date="2020-01-01")
        assert "for documentation." in enactment.text_sequence()[0].text
        enactment.select("for documentation.")
        assert enactment.selected_text() == "…for documentation."

    def test_linked_enactment_without_children(self):
        enactment = LinkedEnactment(
            node="/test/golden",
            heading="The Golden Rule",
            content="Do unto others as you would have them do to you.",
            selection="Do unto others",
            start_date=date(1, 1, 1),
        )
        assert enactment.children == []
        assert enactment.selected_text() == "Do unto others…"

    def test_error_blank_content(self):
        with pytest.raises(ValueError):
            LinkedEnactment(
                node="/test/unwritten",
                heading="The Unwritten Rule",
                textversion=TextVersion(content=""),
                start_date=date(2001, 1, 1),
            )


class TestEnactmentDetails:
    @pytest.mark.vcr
    def test_usc_enactment_is_statute(self, test_client):
        enactment = test_client.read(query="/us/usc/t17/s103", date="2020-01-01")
        assert enactment.sovereign == "us"
        assert enactment.level == "statute"

    def test_str_representation(self, fourth_a, test_client):
        enactment = test_client.read_from_json(fourth_a)
        selection = TextQuoteSelector(
            exact="The right of the people to be secure in their persons"
        )
        enactment.select(selection)
        assert enactment.level == "constitution"
        assert enactment.start_date == date(1791, 12, 15)
        assert "secure in their persons…" in str(enactment)
        assert enactment.node in str(enactment)
        assert "1791-12-15" in str(enactment)

    @pytest.mark.vcr
    def test_sovereign_representation(self, test_client):
        enactment = test_client.read(query="/us")
        assert enactment.code is None
        assert enactment.jurisdiction == "us"

    @pytest.mark.vcr
    def test_constitution_effective_date(self, test_client):
        ex_post_facto_provision = test_client.read(query="/us/const/article/I/8/8")
        assert ex_post_facto_provision.start_date == date(1788, 9, 13)

    @pytest.mark.vcr
    def test_date_and_text_from_path_and_regime(self, test_client):
        """
        This tests different parsing code because the date is
        in the format "dated the 25th of September, 1804"

        This also verifies that the full text of the section
        is selected as the text of the Enactment, even though no
        ``exact``, ``prefix``, or ``suffix`` parameter was
        passed to the TextQuoteSelector constructor.
        """
        amendment_5 = test_client.read(query="/us/const/amendment/V")
        assert amendment_5.start_date == date(1791, 12, 15)
        assert "otherwise infamous crime" in amendment_5.text

    def test_compare_effective_dates(self, fifth_a, fourteenth_dp, test_client):
        amendment_5 = test_client.read_from_json(fifth_a)
        amendment_14 = test_client.read_from_json(fourteenth_dp)
        assert amendment_14.start_date == date(1868, 7, 28)
        assert amendment_5.start_date < amendment_14.start_date

    @pytest.mark.skip(reason="No regulations available via API.")
    def test_regulation_level(self, test_client):
        enactment = test_client.read("/us/cfr/t37/s202.1")
        assert enactment.level == "regulation"

    def test_compare_inbound_citations_on_same_date(self):

        inbound_ref = InboundReference(
            content="or as provided in Section 5",
            reference_text="Section 5",
            target_uri="/test/acts/47/5",
            locations=[
                CitingProvisionLocation(
                    node="/test/acts/47/3/1", start_date=date(2000, 2, 2)
                ),
                CitingProvisionLocation(
                    node="/test/acts/47/7", start_date=date(2000, 2, 2)
                ),
            ],
        )
        assert inbound_ref.latest_location().node == "/test/acts/47/7"


class TestCrossReferences:
    @pytest.mark.vcr()
    def test_no_local_cross_references(self, test_client):
        enactment = test_client.read("/test/acts/47/6D")
        citations = enactment._cross_references
        assert len(citations) == 0

    @pytest.mark.vcr()
    def test_collect_nested_cross_references(self, test_client):
        enactment = test_client.read("/test/acts/47/6D")
        citations = enactment.cross_references()
        assert len(citations) == 1
        assert citations[0].target_uri == "/test/acts/47/6C"
        assert (
            str(citations[0])
            == 'CrossReference(target_uri="/test/acts/47/6C", reference_text="Section 6C")'
        )

    @pytest.mark.vcr()
    def test_locations_of_cross_reference(self, test_client):
        enactment = test_client.read("/test/acts/47/6D")
        assert "Section 6C" in enactment.text
        references = enactment.cross_references()
        citations = test_client.citations_to(references[0])
        assert citations[0].target_uri == "/test/acts/47/6C"


class TestSelectText:
    def test_same_quotation_from_enactments_of_differing_depths(
        self, test_client, section_11_subdivided
    ):
        section = test_client.read_from_json(section_11_subdivided)
        section.select(
            TextQuoteSelector(exact="as they see fit to purchase a beardcoin")
        )
        subsection = test_client.read_from_json(section_11_subdivided["children"][3])
        subsection.select(
            TextQuoteSelector(exact="as they see fit to purchase a beardcoin")
        )
        assert subsection.means(section)
        assert section >= subsection
        assert not section > subsection
        assert not section.text_sequence() > subsection.text_sequence()

    def test_select_text_with_bool(self):
        subsection = Enactment(
            heading="",
            content="The beardcoin shall be a cryptocurrency token…",
            node="/test/acts/47/6C/1",
            start_date=date(2013, 7, 18),
            selection=False,
        )

        section = Enactment(
            heading="Issuance of beardcoin",
            content="Where an exemption is granted",
            node="/test/acts/47/6C",
            children=[subsection],
            end_date=None,
            start_date=date(1935, 4, 1),
        )
        assert section.selected_text() == "Where an exemption is granted…"
        assert "cryptocurrency" not in section.selected_text()

    def test_text_sequence_selected_with_bool(self):
        section = Enactment(
            heading="Issuance of beardcoin",
            content="Where an exemption is granted…",
            node="/test/acts/47/6C",
            children=[],
            end_date=None,
            start_date=date(1935, 4, 1),
        )
        assert section.text_sequence()[0].text == "Where an exemption is granted…"

    def test_select_with_list_of_strings(self, test_client, section_8):
        section = test_client.read_from_json(section_8)
        section.select(
            [
                "Where an officer of the",
                "state or territorial police",
                "finds a person to be wearing a beard",
                "that officer shall in the first instance issue such person a notice to remedy.",
            ]
        )
        selected_text = section.selected_text()
        assert selected_text.startswith(
            "Where an officer of the…state or territorial police…finds"
        )

    def test_str_for_text_sequence(self, test_client, section_11_subdivided):
        section = test_client.read_from_json(section_11_subdivided)
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
            "licenses to such…hairdressers…as they see fit…"
        )

    def test_no_double_spaces_around_repealed_section(self, test_client, section_8):
        section = test_client.read_from_json(section_8["children"][1])
        assert "or remove the beard with" in section.text
        assert "or  remove the beard with" not in section.text

    def test_select_space_between_selected_passages(self, fourteenth_dp, test_client):
        """Test that the space between "property," and "without" is selected."""
        section_1 = test_client.read_from_json(fourteenth_dp)
        section_1.select("without due process of law")
        section_1.select_more("life, liberty, or property,")
        now_selected = section_1.selected_text()
        assert "or property, without" in now_selected


class TestSelectFromEnactment:
    def test_text_of_enactment_subset(self, section_11_together):
        schema = EnactmentSchema()
        combined = schema.load(section_11_together)
        selector = TextQuoteSelector(
            exact="barbers, hairdressers, or other male grooming professionals"
        )
        combined.select(selector)
        sequence = combined.text_sequence()
        assert str(sequence).strip("…").startswith("barbers")

    def test_get_passage(self, section_11_subdivided):
        """
        Use selector to get passage from Enactment without changing which part is selected.

        Checks that `.selected_text()` is the same before and after `.get_passage()`.
        """
        schema = EnactmentSchema()
        section = schema.load(section_11_subdivided)
        section.select(TextPositionSelector(61, 73))
        assert section.selected_text() == "…hairdressers…"
        passage = section.get_passage(TextPositionSelector(112, 127))
        assert passage == "…as they see fit…"
        assert section.selected_text() == "…hairdressers…"

    def test_select_nested_text_with_positions(self, section_11_subdivided):
        phrases = TextPositionSet(
            TextPositionSelector(0, 51),
            TextPositionSelector(61, 73),
            TextPositionSelector(112, 127),
        )
        schema = EnactmentSchema()
        section = schema.load(section_11_subdivided)
        section.select(phrases)
        text_sequence = section.text_sequence()
        assert str(text_sequence) == (
            "The Department of Beards may issue licenses to "
            "such…hairdressers…as they see fit…"
        )

    def test_selection_in_middle_of_enactment(self, test_client, fourth_a):
        result = test_client.read_from_json(fourth_a)
        selector = TextQuoteSelector(
            prefix="and", exact="the persons or things", suffix="to be seized."
        )
        result.select(selector)
        assert result.selected_text().endswith("or things…")

    def test_select_none(self, section_11_subdivided):
        schema = EnactmentSchema()
        combined = schema.load(section_11_subdivided)
        combined.select(False)
        assert combined.selected_text() == ""

    def test_select_none_with_None(self, section_11_subdivided):
        schema = EnactmentSchema()
        combined = schema.load(section_11_subdivided)
        combined.select(None)
        assert combined.selected_text() == ""

    def test_select_all(self, section_11_subdivided):
        """Clear selected text, and then select one subsection."""
        schema = EnactmentSchema()
        combined = schema.load(section_11_subdivided)
        combined.select(None)
        combined.children[3].select()
        assert (
            combined.selected_text()
            == "…as they see fit to purchase a beardcoin from a customer…"
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
        section = schema.load(section_11_subdivided)
        selection = TextPositionSet(
            TextPositionSelector(0, 10), TextPositionSelector(1000, 1010)
        )
        with pytest.raises(ValueError):
            section.children[3].select(selection)

    @pytest.mark.vcr
    def test_get_positions_from_quotes(self, section_11_subdivided):
        schema = EnactmentSchema()
        section = schema.load(section_11_subdivided)
        quotes = [
            TextQuoteSelector(
                exact="The Department of Beards may issue licenses to such"
            ),
            TextQuoteSelector(exact="hairdressers", suffix=", or other male grooming"),
            TextQuoteSelector(exact="as they see fit"),
        ]
        positions = section.convert_quotes_to_position(quotes)
        assert positions == TextPositionSet(
            TextPositionSelector(0, 51),
            TextPositionSelector(61, 73),
            TextPositionSelector(112, 127),
        )

    @pytest.mark.vcr
    def test_text_sequence_has_no_consecutive_Nones(self, test_client):

        amend_14 = test_client.read(query="/us/const/amendment/XIV")
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
        assert section.selected_text() == "…issue licenses…"

    def test_invalid_selector_text(self, section_11_subdivided):
        section_11_subdivided["selection"] = [
            {"exact": "text that doesn't exist in the code"}
        ]
        schema = ExpandableEnactmentSchema()
        with pytest.raises(TextSelectionError):
            _ = schema.load(section_11_subdivided)

    def test_select_text_with_string(self, fourth_a):
        schema = EnactmentSchema()
        fourth_a = schema.load(fourth_a)
        fourth_a.select("The right of the people")
        assert fourth_a.selected_text() == "The right of the people…"

    def test_select_method_clears_previous_selection(self, test_client, section_8):
        old_version = test_client.read_from_json(section_8["children"][1])
        old_selector = TextPositionSet(TextPositionSelector(start=0, end=65),)
        old_version.select(old_selector)
        assert old_version.selected_text() == (
            "Any such person issued a notice to remedy under subsection 1 must…"
        )

    @pytest.mark.vcr
    def test_no_space_before_ellipsis(self, test_client):
        enactment = test_client.read(query="/us/usc/t17/s102/b")
        enactment.select(TextQuoteSelector(suffix="idea, procedure,"))
        assert " …" not in enactment.selected_text()

    @pytest.mark.vcr
    def test_select_near_end_of_section(self, test_client):
        amendment = test_client.read(query="/us/const/amendment/XIV")
        selector = TextPositionSelector(1920, 1980)
        amendment.select(selector)
        assert "The validity of the public debt" in amendment.selected_text()


class TestCompareEnactment:
    @pytest.mark.vcr
    def test_equal_enactment_text(self, test_client):
        """Test provisions with the same text (different dates)."""
        old_version = test_client.read(query="/test/acts/47/6A", date=date(1999, 1, 1))
        new_version = test_client.read(query="/test/acts/47/6A", date=date(2020, 1, 1))
        assert old_version.means(new_version)

    @pytest.mark.vcr
    def test_unequal_enactment_text(self, fourth_a):

        search_clause = fourth_a.copy()
        search_clause["selection"] = [{"suffix": ", and no Warrants"}]

        schema = ExpandableEnactmentSchema()

        fourth_a = schema.load(fourth_a)
        fourth_a.select_all()
        search_clause = schema.load(search_clause)

        assert fourth_a != search_clause
        assert not fourth_a.means(search_clause)
        assert fourth_a >= search_clause

    @pytest.mark.vcr
    def test_not_gt_if_equal(self, test_client):
        """
        Test that __gt__ "implies" operator does not return True for equal Enactments.

        The ISO 8601 format should be valid for the date, even though a datetime
        would have been accepted.
        """
        enactment = test_client.read(query="/test/acts/47/1", date="1999-01-01")
        assert enactment == enactment
        assert not enactment > enactment
        assert enactment >= enactment

    @pytest.mark.vcr
    def test_not_gt_if_equal_with_selection(self, test_client):

        search_clause = test_client.read(query="/us/const/amendment/IV")
        search_clause.select(TextQuoteSelector(suffix=", and no Warrants"))

        assert search_clause == search_clause
        assert search_clause.means(search_clause)
        assert not search_clause > search_clause

    @pytest.mark.vcr
    def test_different_section_same_text(self, test_client, old_section_8, section_8):

        old_version = test_client.read_from_json(
            old_section_8["children"][1]["children"][1]
        )
        new_version = test_client.read_from_json(
            section_8["children"][1]["children"][4]
        )
        assert old_version.means(new_version)

    @pytest.mark.vcr
    def test_combined_section_implies_subdivided_section(
        self, section_11_together, section_11_subdivided
    ):
        schema = EnactmentSchema()
        combined = schema.load(section_11_together)
        combined.select_all()
        subdivided = schema.load(section_11_subdivided)
        subdivided.select_all()
        assert combined >= subdivided
        assert combined > subdivided
        assert combined.text_sequence() > subdivided.text_sequence()

    @pytest.mark.vcr
    def test_more_provisions_implies_fewer(self, test_client, section_8):
        fewer_provisions = test_client.read(
            query="/test/acts/47/8/2", date=date(1999, 1, 1)
        )
        more_provisions = test_client.read_from_json(section_8["children"][1])
        assert more_provisions >= fewer_provisions
        assert more_provisions > fewer_provisions
        assert not fewer_provisions >= more_provisions
        assert not fewer_provisions > more_provisions

    @pytest.mark.vcr
    def test_enactment_subset(self, section_11_together):
        schema = EnactmentSchema()
        combined = schema.load(section_11_together)
        combined.select_all()
        limited = schema.load(section_11_together)
        selector = TextQuoteSelector(
            exact="barbers, hairdressers, or other male grooming professionals"
        )
        limited.select(selector)
        assert not combined.means(limited)
        assert combined > limited

    @pytest.mark.vcr
    def test_same_phrase_different_provisions_same_meaning(self, test_client):

        amend_5 = test_client.read(query="/us/const/amendment/V")
        amend_14 = test_client.read(query="/us/const/amendment/XIV/1")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        amend_5.select(selector)
        amend_14.select(selector)
        assert amend_5.means(amend_14)

    @pytest.mark.vcr
    def test_same_phrase_different_provisions_implication(self, test_client):
        amend_5 = test_client.read(query="/us/const/amendment/V")
        amend_14 = test_client.read(query="/us/const/amendment/XIV/1")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        amend_5.select(selector)
        amend_14.select(selector)
        assert amend_5 >= amend_14

    @pytest.mark.vcr
    def test_same_phrase_selected_in_nested_provision_same_meaning(self, test_client):

        amend_5 = test_client.read(query="/us/const/amendment/V")
        amend_14 = test_client.read(query="/us/const/amendment/XIV")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        amend_5.select(selector)
        amend_14.select(selector)
        assert amend_5.means(amend_14)

    @pytest.mark.vcr
    def test_same_phrase_selected_in_nested_provision_implication(self, test_client):

        amend_5 = test_client.read(query="/us/const/amendment/V")
        amend_14 = test_client.read(query="/us/const/amendment/XIV")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        amend_5.select(selector)
        amend_14.select(selector)
        assert amend_5 >= amend_14

    def test_fail_to_check_enactment_implies_textsequence(self, section_11_subdivided):
        schema = EnactmentSchema()
        subdivided = schema.load(section_11_subdivided)
        text = subdivided.text_sequence()
        with pytest.raises(TypeError):
            _ = subdivided >= text

    def test_fail_to_check_if_enactment_means_textpassage(self, section_11_subdivided):
        schema = EnactmentSchema()
        subdivided = schema.load(section_11_subdivided)
        subdivided.select_all()
        text = subdivided.text_sequence()
        with pytest.raises(TypeError):
            _ = subdivided.means(text.passages[0])

    def test_fail_to_check_if_textpassage_means_enactment(self, section_11_subdivided):
        schema = EnactmentSchema()
        subdivided = schema.load(section_11_subdivided)
        subdivided.select_all()
        text = subdivided.text_sequence()
        with pytest.raises(TypeError):
            _ = text.passages[0].means(subdivided)


class TestAddEnactments:
    def test_add_subset_nested_enactment(self, section_8, test_client):
        """Test that adding an included Enactment returns the same Enactment."""
        greater = test_client.read_from_json(section_8["children"][1])
        lesser = test_client.read_from_json(section_8["children"][1]["children"][0])
        combined = greater + lesser
        assert combined.means(greater)

    @pytest.mark.vcr
    def test_add_superset_nested_enactment(self, section_8, test_client):
        """Test that adding an included Enactment returns the same Enactment."""
        greater = test_client.read_from_json(section_8["children"][1])
        lesser = test_client.read_from_json(section_8["children"][1]["children"][0])
        combined = lesser + greater
        assert combined.means(greater)

    def test_add_shorter_plus_longer(self, fourth_a):
        search_clause = fourth_a.copy()
        search_clause["selection"] = [{"suffix": ", and no Warrants"}]

        schema = ExpandableEnactmentSchema()

        fourth_a = schema.load(fourth_a)
        fourth_a.select_all()
        search_clause = schema.load(search_clause)

        greater_plus_lesser = search_clause + fourth_a

        assert greater_plus_lesser.text == fourth_a.text
        assert greater_plus_lesser.means(fourth_a)

        lesser_plus_greater = fourth_a + search_clause
        assert lesser_plus_greater.text == fourth_a.text
        assert lesser_plus_greater.means(fourth_a)

    def test_add_overlapping_text_selection(self, fourth_a):
        schema = ExpandableEnactmentSchema()
        search = schema.load(fourth_a)
        warrant = schema.load(fourth_a)
        search.select(TextQuoteSelector(suffix=", and no Warrants"))
        warrant.select(
            TextQuoteSelector(
                exact="shall not be violated, and no Warrants shall issue,"
            )
        )
        search.select_more_text_at_current_node(warrant.selection)

        passage = (
            "against unreasonable searches and seizures, "
            + "shall not be violated, "
            + "and no Warrants shall issue,"
        )
        assert passage in search.selected_text()

    def test_non_overlapping_text_selection(self, fourth_a):
        schema = ExpandableEnactmentSchema()
        left = schema.load(fourth_a)
        right = schema.load(fourth_a)
        left.select("The right of the people to be secure in their persons")
        right.select("shall not be violated")
        left.select_more_text_at_current_node(right.selection)
        assert left.selected_text() == (
            "The right of the people to be secure in their persons…"
            "shall not be violated…"
        )

    def test_select_unavailable_text(self, fourth_a):
        schema = ExpandableEnactmentSchema()
        fourth = schema.load(fourth_a)
        with pytest.raises(TextSelectionError):
            fourth.select("right to privacy")

    @pytest.mark.vcr
    def test_add_selection_from_changed_section(self, test_client):
        old_version = test_client.read("/test/acts/47/6D/1", date="1935-04-01")
        new_version = test_client.read("/test/acts/47/6D/1", date="2013-07-18")
        old_version.select("bona fide religious")
        new_version.select("reasons.")
        new_version.select_more_text_from_changed_version(old_version)
        assert new_version.selected_text() == "…bona fide religious…reasons."

    def test_add_selection_from_changed_node_and_subnode(
        self, old_section_8, section_8, test_client
    ):
        """Test that text that has changed subsections can still be added."""
        old_version = test_client.read_from_json(old_section_8)
        new_version = test_client.read_from_json(section_8)
        new_version.select(
            "Any such person issued a notice to remedy under subsection 1 must"
        )
        old_version.select("obtain a beardcoin")
        combined = new_version + old_version
        assert combined.selected_text().endswith("must…obtain a beardcoin…")
        # Test that original Enactments unchanged
        assert "obtain a beardcoin" not in new_version.selected_text()

    def test_add_overlapping_enactments(self, fourth_a):
        schema = EnactmentSchema()
        search = schema.load(fourth_a)
        warrant = schema.load(fourth_a)
        search.select(TextQuoteSelector(suffix=", and no Warrants"))
        warrant.select(
            TextQuoteSelector(
                exact="shall not be violated, and no Warrants shall issue,"
            )
        )
        combined = search + warrant

        passage = (
            "against unreasonable searches and seizures, "
            + "shall not be violated, "
            + "and no Warrants shall issue,"
        )
        assert passage in combined.text
        # Test that original Enactments unchanged
        assert "and no Warrants" not in search.selected_text()

    def test_get_recursive_selection(self, section_8, test_client):
        version = test_client.read_from_json(section_8["children"][1])
        selector = TextPositionSet(TextPositionSelector(start=0, end=65),)
        version.select(selector)
        version.children[4].select("obtain a beardcoin from the Department of Beards")
        selector_set = version.tree_selection()
        ranges = selector_set.ranges()
        assert ranges[0].start == 0
        assert ranges[0].end == 65

        assert ranges[1].start == 218
        assert ranges[1].end == 266

        as_quotes = selector_set.as_quotes(version.text)
        assert as_quotes[1].exact == "obtain a beardcoin from the Department of Beards"

    def test_add_selection_from_child_node(self, section_8, test_client):
        parent_version = test_client.read_from_json(section_8["children"][1])
        parent_selector = TextPositionSet(TextPositionSelector(start=0, end=65),)
        parent_version.select(parent_selector)
        parent_version.children[4].select(
            "obtain a beardcoin from the Department of Beards"
        )
        assert parent_version.selected_text() == (
            "Any such person issued a notice to remedy under subsection 1 must…"
            "obtain a beardcoin from the Department of Beards…"
        )

        child_version = test_client.read_from_json(
            section_8["children"][1]["children"][3]
        )
        child_version.select()

        combined = parent_version + child_version

        assert combined.selected_text() == (
            "Any such person issued a notice to remedy under subsection 1 must…"
            "remove the beard with a laser, or "
            "obtain a beardcoin from the Department of Beards…"
        )

    def test_add_selection_from_parent_node(self, section_8, test_client):
        parent_version = test_client.read_from_json(section_8["children"][1])
        child_version = test_client.read_from_json(
            section_8["children"][1]["children"][3]
        )

        parent_version.select(
            "Any such person issued a notice to remedy under subsection 1 must"
        )
        child_version.select("remove the beard with a laser")

        combined = child_version + parent_version
        assert combined.selected_text() == (
            "Any such person issued a notice to remedy under subsection 1 must…"
            "remove the beard with a laser…"
        )
        # original Enactments should be unchanged
        assert (
            parent_version.selected_text()
            == "Any such person issued a notice to remedy under subsection 1 must…"
        )
        assert child_version.selected_text() == "remove the beard with a laser…"

    def test_fail_to_add_repeated_text_from_changed_version(
        self, section_8, old_section_8, test_client
    ):
        """Fail to place selection because "Department of Beards" occurs twice in this scope."""
        new_version = test_client.read_from_json(section_8)
        new_version.select(
            TextQuoteSelector(
                prefix="Department of Beards, ", exact="Australian Federal Police"
            )
        )

        old_version = test_client.read_from_json(old_section_8)
        old_version.select(
            TextQuoteSelector(prefix="officer of the ", exact="Department of Beards")
        )

        with pytest.raises(ValueError):
            _ = new_version + old_version

    @pytest.mark.vcr
    def test_fail_to_add_non_parent_or_child_enactment(self, test_client):
        left = test_client.read("/test/acts/47/1")
        right = test_client.read("/test/acts/47/2")
        with pytest.raises(ValueError):
            _ = left + right

    def test_fail_to_add_text_not_in_this_version(
        self, old_section_8, section_8, test_client
    ):
        """Fail to add selection from new version because it isn't in the old version."""
        old_version = test_client.read_from_json(old_section_8)
        new_version = test_client.read_from_json(section_8)

        new_version.select(
            TextQuoteSelector(
                prefix="Department of Beards, ", exact="Australian Federal Police"
            )
        )
        old_version.select(
            "Any such person issued a notice to remedy under subsection 1 must"
        )
        new_version.select("remove the beard with a laser")
        with pytest.raises(TextSelectionError):
            _ = old_version + new_version

    def test_fail_to_add_node_not_in_this_version(
        self, old_section_8, section_8, test_client
    ):
        """Fail to add new selection because its node isn't in the old version."""
        old_version = test_client.read_from_json(old_section_8["children"][1])
        new_version = test_client.read_from_json(
            section_8["children"][1]["children"][3]
        )
        with pytest.raises(ValueError):
            _ = old_version + new_version

    @pytest.mark.xfail()
    def test_locate_anchor_by_remembering_prefix(
        self, old_section_8, section_8, test_client
    ):
        """
        Place position selector by remembering prefix from TextQuoteSelector.

        Xfails because the prefix information is lost when the selector
        becomes a position selector.
        """
        old_version = test_client.read_from_json(old_section_8)
        new_version = test_client.read_from_json(section_8)
        new_version.select(
            TextQuoteSelector(
                prefix="Department of Beards, ", exact="Australian Federal Police"
            )
        )

        old_version.select(
            TextQuoteSelector(prefix="officer of the ", exact="Department of Beards")
        )

        combined = new_version + old_version
        assert combined.text == "…Department of Beards…Australian Federal Police…"

    def test_error_for_using_wrong_type_to_select_text(self, section_8, test_client):
        new_version = test_client.read_from_json(section_8)
        with pytest.raises(TypeError):
            new_version.select_more(date(2000, 1, 1))

    def test_able_to_add_subsection_with_text_repeated_elsewhere(
        self, old_section_8, section_8, test_client
    ):
        old_version = test_client.read_from_json(old_section_8)
        new_version = test_client.read_from_json(section_8)
        new_version.select(
            TextQuoteSelector(
                prefix="Department of Beards, ", exact="Australian Federal Police"
            )
        )

        old_version.select(
            TextQuoteSelector(prefix="officer of the ", exact="Department of Beards")
        )

        new_version.children[0].select_more_text_from_changed_version(
            old_version.children[0]
        )

        assert (
            new_version.selected_text()
            == "…Department of Beards, Australian Federal Police…"
        )

    def test_unable_to_add_subsection_with_new_text(
        self, old_section_8, section_8, test_client
    ):
        old_version = test_client.read_from_json(old_section_8)
        new_version = test_client.read_from_json(section_8)
        old_version.select(
            TextQuoteSelector(prefix="officer of the ", exact="Department of Beards")
        )
        new_version.select("remove the beard with electrolysis")
        with pytest.raises(TextSelectionError):
            old_version.select_more_text_from_changed_version(new_version)

    def test_add_string_as_selector(self, section_11_subdivided):
        schema = EnactmentSchema()
        section = schema.load(section_11_subdivided)
        section.select("The Department of Beards may issue licenses to such")
        more = section + "hairdressers"
        assert (
            more.selected_text()
            == "The Department of Beards may issue licenses to such…hairdressers…"
        )

    def test_cannot_select_text_with_citation(self, section_11_subdivided):
        schema = EnactmentSchema()
        section = schema.load(section_11_subdivided)
        cite = section.as_citation()
        with pytest.raises(TypeError):
            section.select_more(cite)


class TestConsolidateEnactments:
    """Test function for combining a list of Enactments."""

    def test_consolidate_enactments(self, fourth_a):
        search_clause = fourth_a.copy()
        search_clause["selection"] = [{"suffix": ", and no Warrants"}]

        warrants_clause = fourth_a.copy()
        warrants_clause["selection"] = [{"prefix": "shall not be violated,"}]

        schema = ExpandableEnactmentSchema()

        search = schema.load(search_clause)
        warrants = schema.load(warrants_clause)

        fourth_amendment = fourth_a.copy()
        fourth_amendment["selection"] = True
        fourth = schema.load(fourth_amendment)

        consolidated = consolidate_enactments([fourth, search, warrants])
        assert len(consolidated) == 1
        assert consolidated[0].means(fourth)

    @pytest.mark.vcr()
    def test_consolidate_adjacent_passages(self, test_client):
        copyright_clause = test_client.read("/us/const/article/I/8/8")
        copyright_statute = test_client.read("/us/usc/t17/s102/b")

        copyright_clause.select(None)
        securing_for_authors = copyright_clause + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        and_inventors = copyright_clause + "and Inventors"
        right_to_writings = (
            copyright_clause + "the exclusive Right to their respective Writings"
        )
        to_combine = [
            copyright_statute,
            securing_for_authors,
            and_inventors,
            right_to_writings,
        ]
        combined = consolidate_enactments(to_combine)
        assert len(combined) == 2
        assert any(
            law.selected_text().startswith("To promote the Progress")
            and law.selected_text().endswith("their respective Writings…")
            for law in combined
        )

    def test_do_not_consolidate_from_different_sections(self, fifth_a, fourteenth_dp):
        schema = EnactmentSchema()

        due_process_5 = schema.load(fifth_a)
        due_process_14 = schema.load(fourteenth_dp)

        due_process_5.select("life, liberty, or property, without due process of law")
        due_process_14.select("life, liberty, or property, without due process of law")

        combined = consolidate_enactments([due_process_5, due_process_14])
        assert len(combined) == 2
