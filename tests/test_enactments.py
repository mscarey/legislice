from datetime import date
import os

from anchorpoint import TextQuoteSelector, TextPositionSelector
from anchorpoint.textselectors import TextPositionSet, TextSelectionError, Range
from dotenv import load_dotenv
from pydantic import ValidationError
import pytest

from legislice.citations import CodeLevel
from legislice.download import Client
from legislice.enactments import (
    CitingProvisionLocation,
    Enactment,
    EnactmentPassage,
    InboundReference,
    TextVersion,
    consolidate_enactments,
)

load_dotenv()

TOKEN = os.getenv("LEGISLICE_API_TOKEN")
API_ROOT = "https://authorityspoke.com/api/v1"


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
        assert s1.nested_children == []
        assert "Enactment(node='/test/acts/47/1'" in repr(s1)

    def test_init_enactment_with_nesting(self):
        subsection = Enactment(
            heading="",
            text_version="The beardcoin shall be a cryptocurrency token…",
            node="/test/acts/47/6C/1",
            start_date=date(2013, 7, 18),
        )

        section = Enactment(
            heading="Issuance of beardcoin",
            text_version="Where an exemption is granted under section 6…",
            node="/test/acts/47/6C",
            children=[subsection],
            end_date=None,
            start_date=date(1935, 4, 1),
        )

        assert section.children[0].content.startswith("The beardcoin shall")

    def test_create_TextPositionSet_on_init(self, section_11_subdivided):
        len_s11 = len(section_11_subdivided["text_version"]["content"])
        data = {
            "enactment": section_11_subdivided,
            "selection": {"positions": [{"start": 0, "end": len_s11}]},
        }
        start_point = len_s11 + len(
            section_11_subdivided["children"][0]["text_version"]["content"]
        )

        margin = 2
        expected = "hairdressers"
        data["selection"]["positions"].append(
            {"start": start_point + margin, "end": start_point + margin + len(expected)}
        )
        result = EnactmentPassage(**data)
        assert isinstance(result.selection, TextPositionSet)
        assert (
            result.selected_text()
            == "The Department of Beards may issue licenses to such…hairdressers…"
        )


class TestLinkedEnactment:
    @pytest.mark.vcr
    def test_text_sequence_for_linked_enactment(self, test_client):
        enactment = test_client.read(query="/test", date="2020-01-01")
        assert "for documentation." in enactment.text
        selected = enactment.select("for documentation.")
        assert selected.selected_text() == "…for documentation."
        assert "for documentation" in selected.text

    def test_enactment_without_children(self):
        enactment = Enactment(
            node="/test/golden",
            heading="The Golden Rule",
            text_version="Do unto others as you would have them do to you.",
            start_date=date(1, 1, 1),
        )
        assert enactment.children == []
        new = enactment.select("Do unto others")
        assert new.selected_text() == "Do unto others…"

    def test_error_blank_content(self):
        with pytest.raises(ValueError):
            Enactment(
                node="/test/unwritten",
                heading="The Unwritten Rule",
                textversion=TextVersion(content=""),
                start_date=date(2001, 1, 1),
            )

    @pytest.mark.vcr
    def test_csl_cite_for_usc(self, test_client):
        enactment = test_client.read(query="/us/usc", date="2020-01-01")
        assert '"container-title": "U.S. Code"' in enactment.csl_json()


class TestEnactmentDetails:
    @pytest.mark.vcr
    def test_usc_enactment_is_statute(self, test_client):
        enactment = test_client.read(query="/us/usc/t17/s103", date="2020-01-01")
        assert enactment.sovereign == "us"
        assert enactment.level == CodeLevel.STATUTE

    @pytest.mark.vcr
    def test_str_representation(self, fourth_a, test_client):
        enactment = test_client.read_from_json(fourth_a)
        selection = TextQuoteSelector(
            exact="The right of the people to be secure in their persons"
        )
        new = enactment.select(selection)
        assert new.level == CodeLevel.CONSTITUTION
        assert new.start_date == date(1791, 12, 15)
        assert "secure in their persons…" in str(new)
        assert enactment.node in str(new)
        assert "1791-12-15" in str(new)

    def test_node_parts(self, section_11_subdivided):
        enactment = Enactment(**section_11_subdivided)
        passage = enactment.select_all()
        assert passage.section == "11"
        assert passage.title == "47"
        assert passage.code == "acts"
        assert passage.jurisdiction == "test"
        assert passage.sovereign == "test"

    def test_csl_json_fields(self, test_client, section_11_subdivided):
        section = test_client.read_from_json(section_11_subdivided)
        cite_json = section.csl_json()
        assert "event-date" in cite_json

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
        citations = enactment.citations
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
    client = Client(api_token=TOKEN)

    def test_same_quotation_from_enactments_of_differing_depths(
        self, test_client, section_11_subdivided
    ):
        section = test_client.read_from_json(section_11_subdivided)
        selection = section.select(
            TextQuoteSelector(exact="as they see fit to purchase a beardcoin")
        )
        subsection = test_client.read_from_json(section_11_subdivided["children"][3])
        sub_selection = subsection.select(
            TextQuoteSelector(exact="as they see fit to purchase a beardcoin")
        )
        assert sub_selection.means(selection)
        assert selection >= sub_selection
        assert not selection > sub_selection
        assert not selection.text_sequence() > sub_selection.text_sequence()

    def test_select_text_of_parent_section(self):
        subsection = Enactment(
            heading="",
            text_version="The beardcoin shall be a cryptocurrency token…",
            node="/test/acts/47/6C/1",
            start_date=date(2013, 7, 18),
        )

        section = Enactment(
            heading="Issuance of beardcoin",
            text_version="Where an exemption is granted",
            node="/test/acts/47/6C",
            children=[subsection],
            end_date=None,
            start_date=date(1935, 4, 1),
        )
        selection = section.select(section.content)
        assert selection.selected_text() == "Where an exemption is granted…"
        assert "cryptocurrency" not in selection.selected_text()
        assert str(section) == "/test/acts/47/6C (1935-04-01)"
        assert str(subsection) == "/test/acts/47/6C/1 (2013-07-18)"

    def test_text_sequence_selected_with_bool(self):
        section = Enactment(
            heading="Issuance of beardcoin",
            text_version="Where an exemption is granted…",
            node="/test/acts/47/6C",
            children=[],
            end_date=None,
            start_date=date(1935, 4, 1),
        )
        selection = section.select(section.text_version.content)
        assert selection.text_sequence()[0].text == "Where an exemption is granted…"

    def test_select_with_list_of_strings(self, test_client, section_8):
        section = test_client.read_from_json(section_8)
        selection = section.select(
            [
                "Where an officer of the",
                "state or territorial police",
                "finds a person to be wearing a beard",
                "that officer shall in the first instance issue such person a notice to remedy.",
            ]
        )
        selected_text = selection.selected_text()
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
        selection = section.select(quotes)
        text_sequence = selection.text_sequence()
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
        selection = section_1.select("without due process of law")
        selection.select_more("life, liberty, or property,")
        now_selected = selection.selected_text()
        assert "or property, without" in now_selected


class TestSelectFromEnactment:
    client = Client(api_token=TOKEN)

    def test_text_of_enactment_subset(self, section_11_together):
        combined = Enactment(**section_11_together)
        selector = TextQuoteSelector(
            exact="barbers, hairdressers, or other male grooming professionals"
        )
        passage = combined.select(selector)
        sequence = passage.text_sequence()
        assert str(sequence).strip("…").startswith("barbers")

    def test_get_passage(self, section_11_subdivided):
        """
        Use selector to get passage from Enactment without changing which part is selected.

        Checks that `.selected_text()` is the same before and after `.get_passage()`.
        """
        section = Enactment(**section_11_subdivided)
        passage = section.select(TextPositionSelector(start=61, end=73))
        assert passage.selected_text() == "…hairdressers…"
        fit_passage = section.get_string(TextPositionSelector(start=112, end=127))
        assert fit_passage == "…as they see fit…"

    def test_get_child_passage(self, section_11_subdivided):
        """
        Use selector to get passage from child of Enactment.
        """
        section = Enactment(**section_11_subdivided)
        passage = section.select(
            [
                TextQuoteSelector(
                    exact="The Department of Beards may issue licenses to"
                ),
                TextQuoteSelector(exact="professionals"),
            ]
        )
        assert passage.node == "/test/acts/47/11"
        assert passage.selected_text().endswith("licenses to…professionals…")
        assert len(passage.selection.ranges()) == 2
        assert passage.selection.ranges()[0] == Range(start=0, end=46)
        assert passage.selection.ranges()[1] == Range(start=98, end=111)

        child_passage = passage.child_passages[2]
        assert len(child_passage.selection.ranges()) == 1
        assert child_passage.selected_text() == "…professionals"
        assert child_passage.selection.ranges()[0] == Range(start=20, end=33)
        assert child_passage.node == "/test/acts/47/11/iii"

    def test_select_nested_text_with_positions(self, section_11_subdivided):
        phrases = TextPositionSet(
            positions=[
                TextPositionSelector(start=0, end=51),
                TextPositionSelector(start=61, end=73),
                TextPositionSelector(start=112, end=127),
            ],
        )
        section = Enactment(**section_11_subdivided)
        passage = section.select(phrases)
        text_sequence = passage.text_sequence()
        assert str(text_sequence) == (
            "The Department of Beards may issue licenses to "
            "such…hairdressers…as they see fit…"
        )

    def test_selection_in_middle_of_enactment(self, test_client, fourth_a):
        result = test_client.read_from_json(fourth_a)
        selector = TextQuoteSelector(
            prefix="and", exact="the persons or things", suffix="to be seized."
        )
        passage = result.select(selector)
        assert passage.selected_text().endswith("or things…")

    def test_select_all_of_empty_enactment(self):
        empty = Enactment(
            node="/us/usc/t1/s101",
            heading="No text",
            text_version="",
            start_date=date(1935, 4, 1),
        )
        passage = empty.select_all()
        assert passage.selected_text() == ""

    def test_select_none(self, section_11_subdivided):
        combined = Enactment(**section_11_subdivided)
        passage = combined.select(False)
        assert passage.selected_text() == ""

    def test_select_none_with_None(self, section_11_subdivided):
        combined = Enactment(**section_11_subdivided)
        passage = combined.select(None)
        assert passage.selected_text() == ""

    def test_select_all(self, section_11_subdivided):
        """Clear selected text, and then select one subsection."""
        combined = Enactment(**section_11_subdivided)
        passage = combined.select(None)
        assert passage.enactment.node == "/test/acts/47/11"
        sub_passage = passage.enactment.children[3].select_all()
        assert (
            sub_passage.selected_text()
            == "as they see fit to purchase a beardcoin from a customer"
        )
        assert sub_passage.enactment.node == "/test/acts/47/11/iii-con"

    def test_select_all_nested(self, section_11_subdivided):
        """Clear selected text, and then select one subsection."""
        section = Enactment(**section_11_subdivided)
        passage = section.select()
        assert passage.selected_text().startswith("The Department of Beards")

    def test_error_for_unusable_selector(self, section_11_subdivided):
        section = Enactment(**section_11_subdivided)
        selection = TextPositionSet(
            positions=[
                TextPositionSelector(start=0, end=10),
                TextPositionSelector(start=1000, end=1010),
            ]
        )
        with pytest.raises(ValueError):
            section.children[3].select(selection)

    @pytest.mark.vcr
    def test_get_positions_from_quotes(self, section_11_subdivided):
        section = Enactment(**section_11_subdivided)
        quotes = [
            TextQuoteSelector(
                exact="The Department of Beards may issue licenses to such"
            ),
            TextQuoteSelector(exact="hairdressers", suffix=", or other male grooming"),
            TextQuoteSelector(exact="as they see fit"),
        ]
        positions = section.convert_quotes_to_position(quotes)
        assert positions == TextPositionSet(
            positions=[
                TextPositionSelector(start=0, end=51),
                TextPositionSelector(start=61, end=73),
                TextPositionSelector(start=112, end=127),
            ],
        )

    @pytest.mark.vcr
    def test_text_sequence_has_no_consecutive_Nones(self, test_client):

        amend_14 = test_client.read(query="/us/const/amendment/XIV")
        selector = TextQuoteSelector(exact="life, liberty, or property")
        passage = amend_14.select(selector)
        selected_list = passage.text_sequence()

        assert len(selected_list) == 3
        assert selected_list[0] is None
        assert selected_list[1].text == "life, liberty, or property"
        assert selected_list[2] is None

    def test_select_with_position_selector(self, section_11_together):
        section = Enactment(**section_11_together)
        passage = section.select(TextPositionSelector(start=29, end=43))
        assert passage.selected_text() == "…issue licenses…"

    def test_invalid_selector_text(self, section_11_subdivided):
        selector = TextQuoteSelector(exact="text that doesn't exist in the code")
        enactment = Enactment(**section_11_subdivided)

        with pytest.raises(TextSelectionError):
            enactment.select(selector)

    def test_select_text_with_string(self, fourth_a):
        section = Enactment(**fourth_a)
        passage = section.select("The right of the people")
        assert passage.selected_text() == "The right of the people…"

    def test_select_method_clears_previous_selection(self, test_client, section_8):
        old_version = test_client.read_from_json(section_8["children"][1])
        old_selector = TextPositionSet(
            positions=TextPositionSelector(start=0, end=65),
        )
        passage = old_version.select(old_selector)
        assert passage.selected_text() == (
            "Any such person issued a notice to remedy under subsection 1 must…"
        )

    @pytest.mark.vcr
    def test_no_space_before_ellipsis(self, test_client):
        enactment = test_client.read(query="/us/usc/t17/s102/b")
        passage = enactment.select(TextQuoteSelector(suffix="idea, procedure,"))
        assert " …" not in passage.selected_text()

    @pytest.mark.vcr
    def test_select_near_end_of_section(self):
        amendment = self.client.read(query="/us/const/amendment/XIV")
        selector = TextPositionSelector(start=1920, end=1980)
        passage = amendment.select(selector)
        assert "The validity of the public debt" in passage.selected_text()
        set_passage = amendment.select(
            TextPositionSet(
                positions=[
                    TextPositionSelector(start=1921, end=1973),
                    TextPositionSelector(start=2111, end=2135),
                ]
            )
        )
        expected = "…The validity of the public debt of the United States…shall not be questioned.…"
        assert set_passage.selected_text() == expected


class TestCompareEnactment:
    @pytest.mark.vcr
    def test_equal_enactment_text(self, test_client):
        """Test provisions with the same text (different dates)."""
        old_version = test_client.read(query="/test/acts/47/6A", date=date(1999, 1, 1))
        new_version = test_client.read(query="/test/acts/47/6A", date=date(2020, 1, 1))
        assert old_version.means(new_version)

    @pytest.mark.vcr
    def test_unequal_enactment_text(self, fourth_a):

        enactment = Enactment(**fourth_a)
        selector = TextQuoteSelector(suffix=", and no Warrants")
        search_clause = enactment.select(selector)

        whole_provision = enactment.select_all()

        assert whole_provision != search_clause
        assert not whole_provision.means(search_clause)
        assert whole_provision >= search_clause
        assert whole_provision > search_clause

    @pytest.mark.vcr
    def test_not_gt_if_equal(self, test_client):
        """
        Test that __gt__ "implies" operator does not return True for equal Enactments.

        The ISO 8601 format should be valid for the date, even though a datetime
        would have been accepted.
        """
        enactment = test_client.read(query="/test/acts/47/1", date="1999-01-01")
        passage = enactment.select_all()
        assert passage == passage
        assert not passage > passage
        assert passage >= passage

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
        combined = Enactment(**section_11_together)
        passage = combined.select_all()
        subdivided = Enactment(**section_11_subdivided)
        divided_passage = subdivided.select_all()
        assert passage >= divided_passage
        assert not passage > divided_passage
        assert passage.text_sequence() >= divided_passage.text_sequence()

    def test_passage_does_not_imply_text_sequence(
        self, section_11_together, section_11_subdivided
    ):
        combined = Enactment(**section_11_together)
        passage = combined.select_all()
        subdivided = Enactment(**section_11_subdivided)
        divided_passage = subdivided.select_all()
        with pytest.raises(TypeError):
            passage >= divided_passage.text_sequence()

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
        combined = Enactment(**section_11_together)
        passage = combined.select_all()
        selector = TextQuoteSelector(
            exact="barbers, hairdressers, or other male grooming professionals"
        )
        limited = combined.select(selector)
        assert not passage.means(limited)
        assert combined > limited

    def test_cannot_compare_passage_with_text_version(self, section_8):
        enactment = Enactment(**section_8)
        passage = enactment.select_all()
        with pytest.raises(TypeError):
            passage.means(enactment.text_version)

    @pytest.mark.vcr
    def test_same_phrase_different_provisions_same_meaning(self, test_client):

        amend_5 = test_client.read(query="/us/const/amendment/V")
        amend_14 = test_client.read(query="/us/const/amendment/XIV/1")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        left = amend_5.select(selector)
        right = amend_14.select(selector)
        assert left.means(right)

    @pytest.mark.vcr
    def test_same_phrase_different_provisions_implication(self, test_client):
        amend_5 = test_client.read(query="/us/const/amendment/V")
        amend_14 = test_client.read(query="/us/const/amendment/XIV/1")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        left = amend_5.select(selector)
        right = amend_14.select(selector)
        assert left >= right

    @pytest.mark.vcr
    def test_same_phrase_selected_in_nested_provision_same_meaning(self, test_client):

        amend_5 = test_client.read(query="/us/const/amendment/V")
        amend_14 = test_client.read(query="/us/const/amendment/XIV")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        left = amend_5.select(selector)
        right = amend_14.select(selector)
        assert left.means(right)

    @pytest.mark.vcr
    def test_same_phrase_selected_in_nested_provision_implication(self, test_client):

        amend_5 = test_client.read(query="/us/const/amendment/V")
        amend_14 = test_client.read(query="/us/const/amendment/XIV")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        left = amend_5.select(selector)
        right = amend_14.select(selector)
        assert left >= right

    def test_fail_to_check_enactment_implies_textsequence(self, section_11_subdivided):
        subdivided = Enactment(**section_11_subdivided)
        text = subdivided.text_sequence()
        with pytest.raises(TypeError):
            _ = subdivided >= text

    def test_fail_to_check_if_enactment_means_textpassage(self, section_11_subdivided):
        subdivided = Enactment(**section_11_subdivided)
        subdivided.select_all()
        text = subdivided.text_sequence()
        with pytest.raises(TypeError):
            _ = subdivided.means(text.passages[0])

    def test_fail_to_check_if_textpassage_means_enactment(self, section_11_subdivided):
        subdivided = Enactment(**section_11_subdivided)
        subdivided.select_all()
        text = subdivided.text_sequence()
        with pytest.raises(TypeError):
            _ = text.passages[0].means(subdivided)


class TestAddEnactments:
    def test_add_subset_nested_enactment(self, section_8, test_client):
        """Test that adding an included Enactment returns the same Enactment."""
        greater = test_client.read_from_json(section_8["children"][1])
        lesser = test_client.read_from_json(section_8["children"][1]["children"][0])

        greater_passage = greater.select_all()
        lesser_passage = lesser.select_all()

        combined = greater_passage + lesser_passage

        assert combined.means(greater_passage)

        assert combined.means(greater_passage)

    @pytest.mark.vcr
    def test_add_superset_nested_enactment(self, section_8, test_client):
        """Test that adding an included Enactment returns the same Enactment."""
        greater = test_client.read_from_json(section_8["children"][1])
        lesser = test_client.read_from_json(section_8["children"][1]["children"][0])
        greater_passage = greater.select_all()
        lesser_passage = lesser.select_all()

        combined = lesser_passage + greater_passage

        assert combined.means(greater_passage)

    @pytest.mark.vcr
    def test_add_enactment_to_passage(self, section_8, test_client):
        """Test that adding an included Enactment returns the same Enactment."""
        greater = test_client.read_from_json(section_8["children"][1])
        passage = greater.select(
            "Any such person issued a notice to remedy under subsection 1 must"
        )
        lesser = test_client.read_from_json(section_8["children"][1]["children"][0])

        combined = passage + lesser

        selected_text = combined.selected_text()
        assert "Any such person" in selected_text
        assert "must…shave" in selected_text

    def test_add_shorter_plus_longer(self, fourth_a):
        fourth_a = Enactment(**fourth_a)
        selector = TextQuoteSelector(suffix=", and no Warrants")
        amendment = fourth_a.select_all()
        search_clause = fourth_a.select(selector)

        greater_plus_lesser = amendment + search_clause

        assert greater_plus_lesser.text == amendment.text
        assert greater_plus_lesser.means(amendment)

        lesser_plus_greater = search_clause + amendment
        assert lesser_plus_greater.text == amendment.text
        assert lesser_plus_greater.means(amendment)

    def test_add_overlapping_text_selection(self, fourth_a):
        enactment = Enactment(**fourth_a)
        passage = enactment.select(TextQuoteSelector(suffix=", and no Warrants"))
        new = enactment.make_selection(
            TextQuoteSelector(
                exact="shall not be violated, and no Warrants shall issue,"
            )
        )
        passage.select_more_text_at_current_node(new)

        expected = (
            "against unreasonable searches and seizures, "
            + "shall not be violated, "
            + "and no Warrants shall issue,"
        )
        assert expected in passage.selected_text()

    def test_non_overlapping_text_selection(self, fourth_a):
        enactment = Enactment(**fourth_a)
        left = enactment.select("The right of the people to be secure in their persons")
        right = enactment.select("shall not be violated")
        left.select_more_text_at_current_node(right.selection)
        assert left.selected_text() == (
            "The right of the people to be secure in their persons…"
            "shall not be violated…"
        )

    def test_limit_selected_text(self, fourth_a):
        enactment = Enactment(**fourth_a)
        passage = enactment.select(
            "The right of the people to be secure in their persons"
        )
        passage.select_more("shall not be violated")
        assert passage.selected_text() == (
            "The right of the people to be secure in their persons…"
            "shall not be violated…"
        )
        passage.limit_selection(start=40)
        assert passage.selected_text() == "…their persons…shall not be violated…"

    def test_change_selection_to_all(self, fourth_a):
        enactment = Enactment(**fourth_a)
        passage = enactment.select("right of the people")
        assert passage.selected_text() == ("…right of the people…")
        passage.select_all()
        assert passage.selected_text().startswith("The right of the people to")

    def test_select_unavailable_text(self, fourth_a):
        fourth = Enactment(**fourth_a)
        with pytest.raises(TextSelectionError):
            fourth.select("right to privacy")

    @pytest.mark.vcr
    def test_add_selection_from_changed_section(self, test_client):
        old_version = test_client.read("/test/acts/47/6D/1", date="1935-04-01")
        new_version = test_client.read("/test/acts/47/6D/1", date="2013-07-18")
        old = old_version.select("bona fide religious")
        new = new_version.select("reasons.")
        new.select_more_text_from_changed_version(old)
        assert new.selected_text() == "…bona fide religious…reasons."

    def test_add_selection_from_changed_node_and_subnode(
        self, old_section_8, section_8, test_client
    ):
        """Test that text that has changed subsections can still be added."""
        old_version = test_client.read_from_json(old_section_8)
        new_version = test_client.read_from_json(section_8)
        new_selection = new_version.select(
            "Any such person issued a notice to remedy under subsection 1 must"
        )
        old_selection = old_version.select("obtain a beardcoin")
        combined = new_selection + old_selection
        assert combined.selected_text().endswith("must…obtain a beardcoin…")
        # Test that original Enactments unchanged
        assert "obtain a beardcoin" not in new_selection.selected_text()

    def test_add_overlapping_enactments(self, fourth_a):
        enactment = Enactment(**fourth_a)
        search = enactment.select(TextQuoteSelector(suffix=", and no Warrants"))
        warrant = enactment.select(
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
        selector = TextPositionSet(
            positions=TextPositionSelector(start=0, end=65),
        )
        passage = version.select(selector)
        passage.select_more("obtain a beardcoin from the Department of Beards")

        ranges = passage.selection.ranges()
        assert ranges[0].start == 0
        assert ranges[0].end == 65

        assert ranges[1].start == 218
        assert ranges[1].end == 266

        as_quotes = passage.selection.as_quotes(version.text)
        assert as_quotes[1].exact == "obtain a beardcoin from the Department of Beards"

    def test_add_selection_from_child_node(self, section_8, test_client):
        parent_version = test_client.read_from_json(section_8["children"][1])
        parent_selector = TextPositionSet(
            positions=TextPositionSelector(start=0, end=65),
        )
        passage = parent_version.select(parent_selector)
        passage.select_more("obtain a beardcoin from the Department of Beards")
        assert passage.selected_text() == (
            "Any such person issued a notice to remedy under subsection 1 must…"
            "obtain a beardcoin from the Department of Beards…"
        )

        child_version = test_client.read_from_json(
            section_8["children"][1]["children"][3]
        )
        child_passage = child_version.select()

        combined = passage + child_passage

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

        parent_passage = parent_version.select(
            "Any such person issued a notice to remedy under subsection 1 must"
        )
        child_passage = child_version.select("remove the beard with a laser")

        combined = child_passage + parent_passage
        assert combined.selected_text() == (
            "Any such person issued a notice to remedy under subsection 1 must…"
            "remove the beard with a laser…"
        )
        # original Enactments should be unchanged
        assert (
            parent_passage.selected_text()
            == "Any such person issued a notice to remedy under subsection 1 must…"
        )
        assert child_passage.selected_text() == "remove the beard with a laser…"

    def test_fail_to_add_repeated_text_from_changed_version(
        self, section_8, old_section_8, test_client
    ):
        """Fail to place selection because "Department of Beards" occurs twice in this scope."""
        new_version = test_client.read_from_json(section_8)
        new_passage = new_version.select(
            TextQuoteSelector(
                prefix="Department of Beards, ", exact="Australian Federal Police"
            )
        )

        old_version = test_client.read_from_json(old_section_8)
        old_passage = old_version.select(
            TextQuoteSelector(prefix="officer of the ", exact="Department of Beards")
        )

        with pytest.raises(TextSelectionError):
            new_passage + old_passage

    @pytest.mark.vcr
    def test_fail_to_add_non_parent_or_child_enactment(self, test_client):
        left = test_client.read("/test/acts/47/1")
        right = test_client.read("/test/acts/47/2")
        left_passage = left.select()
        right_passage = right.select()
        with pytest.raises(ValueError):
            _ = left_passage + right_passage

    def test_fail_to_add_text_not_in_this_version(
        self, old_section_8, section_8, test_client
    ):
        """Fail to add selection from new version because it isn't in the old version."""
        old_version = test_client.read_from_json(old_section_8)
        new_version = test_client.read_from_json(section_8)

        old_passage = old_version.select(
            "Any such person issued a notice to remedy under subsection 1 must"
        )
        new_passage = new_version.select("remove the beard with a laser")
        with pytest.raises(TextSelectionError):
            old_passage + new_passage

    def test_fail_to_add_node_not_in_this_version(
        self, old_section_8, section_8, test_client
    ):
        """Fail to add new selection because its node isn't in the old version."""
        old_version = test_client.read_from_json(old_section_8["children"][1])
        new_version = test_client.read_from_json(
            section_8["children"][1]["children"][3]
        )
        old_passage = old_version.select()
        new_passage = new_version.select()
        with pytest.raises(TextSelectionError):
            old_passage + new_passage

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
            new_version.select(date(2000, 1, 1))

    def test_get_rangedict(self, old_section_8, test_client):
        old_version = test_client.read_from_json(old_section_8)
        result = old_version.rangedict()
        memo = result[3]
        assert memo.content.startswith("Where an officer")
        assert memo.start_date == date(1935, 4, 1)

    def test_passage_start_date_is_latest_amendment(self, section_8, test_client):
        new_version = test_client.read_from_json(section_8)
        new_passage = new_version.select("remove the beard with electrolysis")
        assert new_passage.start_date == date(2013, 7, 18)
        assert new_passage.end_date is None

    def test_repealed_passage_end_date_is_earliest_found(
        self, old_section_8, test_client
    ):
        old_version = test_client.read_from_json(old_section_8)
        old_passage = old_version.select(
            TextQuoteSelector(prefix="officer of the ", exact="Department of Beards")
        )
        old_passage.select_more("obtain a beardcoin from the Department of Beards")
        # adding an earlier end date
        old_passage.enactment.children[1].children[2].end_date = date(2001, 1, 1)
        old_passage.select_more("within 14 days of such notice")
        assert old_passage.start_date == date(1935, 4, 1)
        assert old_passage.end_date == date(2001, 1, 1)

    def test_unable_to_add_subsection_with_new_text(
        self, old_section_8, section_8, test_client
    ):
        old_version = test_client.read_from_json(old_section_8)
        new_version = test_client.read_from_json(section_8)
        old_passage = old_version.select(
            TextQuoteSelector(prefix="officer of the ", exact="Department of Beards")
        )
        new_passage = new_version.select("remove the beard with electrolysis")
        with pytest.raises(TextSelectionError):
            old_passage + new_passage

    def test_add_string_as_selector(self, section_11_subdivided):
        section = Enactment(**section_11_subdivided)
        passage = section.select("The Department of Beards may issue licenses to such")
        more = passage + "hairdressers"
        assert (
            more.selected_text()
            == "The Department of Beards may issue licenses to such…hairdressers…"
        )

    def test_clear_selection(self, section_8):
        section = Enactment(**section_8)
        passage = section.select_all()
        passage.clear_selection()
        assert passage.selected_text() == ""

    def test_select_from_passage(self, section_8):
        section = Enactment(**section_8)
        passage = section.select_all()
        passage.select("Australian Defence Force")
        assert passage.selected_text() == "…Australian Defence Force…"

    def test_cannot_select_text_with_citation(self, section_11_subdivided):
        section = Enactment(**section_11_subdivided)
        cite = section.as_citation()
        with pytest.raises(ValidationError):
            section.select(cite)


class TestConsolidateEnactments:
    """Test function for combining a list of Enactments."""

    def test_consolidate_enactments(self, fourth_a):
        enactment = Enactment(**fourth_a)
        search_selector = TextQuoteSelector(suffix=", and no Warrants")
        search_clause = enactment.select(search_selector)

        warrants_selector = TextQuoteSelector(prefix="shall not be violated,")
        warrants_clause = enactment.select(warrants_selector)

        fourth_amendment = enactment.select_all()

        consolidated = consolidate_enactments(
            [fourth_amendment, search_clause, warrants_clause]
        )
        assert len(consolidated) == 1
        assert consolidated[0].means(fourth_amendment)

    @pytest.mark.vcr()
    def test_consolidate_adjacent_passages(self, test_client):
        copyright_clause = test_client.read("/us/const/article/I/8/8")
        copyright_statute = test_client.read("/us/usc/t17/s102/b").select_all()

        selection = copyright_clause.select(None)
        securing_for_authors = selection + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        and_inventors = selection + "and Inventors"
        right_to_writings = (
            selection + "the exclusive Right to their respective Writings"
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

        due_process_5 = Enactment(**fifth_a)
        due_process_14 = Enactment(**fourteenth_dp)

        passage = "life, liberty, or property, without due process of law"
        quote_5 = due_process_5.select(passage)
        quote_14 = due_process_14.select(passage)

        combined = consolidate_enactments([quote_5, quote_14])
        assert len(combined) == 2
