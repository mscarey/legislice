from datetime import date
import os

from anchorpoint import TextQuoteSelector, TextPositionSelector
from anchorpoint.textselectors import TextPositionSet, TextSelectionError
from dotenv import load_dotenv
import pytest

from legislice.download import Client
from legislice.enactments import Enactment, consolidate_enactments
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


class TestLinkedEnactment:
    client = Client(api_token=TOKEN)

    @pytest.mark.vcr()
    def test_text_sequence_for_linked_enactment(self):
        enactment = self.client.read(path="/test", date="2020-01-01")
        assert "for documentation." in enactment.text_sequence()[0].text

    @pytest.mark.vcr()
    def test_select_text_in_linked_enactment(self):
        enactment = self.client.read(path="/test", date="2020-01-01")
        enactment.select("for documentation.")
        assert enactment.selected_text() == "...for documentation."


class TestEnactmentDetails:
    client = Client(api_token=TOKEN)

    @pytest.mark.vcr()
    def test_usc_enactment_is_statute(self):
        enactment = self.client.read(path="/us/usc/t17/s103", date="2020-01-01")
        assert enactment.sovereign == "us"
        assert enactment.level == "statute"

    @pytest.mark.vcr()
    def test_str_representation(self):
        enactment = self.client.read(path="/us/const/amendment/IV")
        selection = TextQuoteSelector(
            exact="The right of the people to be secure in their persons"
        )
        enactment.select(selection)
        assert enactment.level == "constitution"
        assert enactment.start_date == date(1791, 12, 15)
        assert "secure in their persons..." in str(enactment)
        assert enactment.node in str(enactment)
        assert enactment.source == enactment.node
        assert "1791-12-15" in str(enactment)

    @pytest.mark.vcr()
    def test_sovereign_representation(self):
        enactment = self.client.read(path="/us")
        assert enactment.code is None
        assert enactment.jurisdiction == "us"

    @pytest.mark.vcr()
    def test_constitution_effective_date(self):
        ex_post_facto_provision = self.client.read(path="/us/const/article/I/9/3")
        assert ex_post_facto_provision.start_date == date(1788, 9, 13)

    @pytest.mark.vcr()
    def test_date_and_text_from_path_and_regime(self):
        """
        This tests different parsing code because the date is
        in the format "dated the 25th of September, 1804"

        This also verifies that the full text of the section
        is selected as the text of the Enactment, even though no
        ``exact``, ``prefix``, or ``suffix`` parameter was
        passed to the TextQuoteSelector constructor.
        """
        amendment_12 = self.client.read(path="/us/const/amendment/XII")
        assert amendment_12.start_date == date(1804, 9, 25)
        assert "Electors shall meet" in amendment_12.text

    @pytest.mark.vcr()
    def test_compare_effective_dates(self):
        amendment_5 = self.client.read(path="/us/const/amendment/XII")
        amendment_14 = self.client.read(path="/us/const/amendment/XIV")
        assert amendment_14.start_date == date(1868, 7, 28)
        assert amendment_5.start_date < amendment_14.start_date


class TestSelectText:
    client = Client(api_token=TOKEN)

    @pytest.mark.vcr()
    def test_get_all_text(self):
        section = self.client.read(path="/test/acts/47/11")
        assert "barbers, hairdressers, or other" in section.text

    @pytest.mark.vcr()
    def test_same_quotation_from_enactments_of_differing_depths(self):
        section = self.client.read(path="/test/acts/47/6C")
        section.select(
            TextQuoteSelector(exact="The beardcoin shall be a cryptocurrency")
        )
        subsection = self.client.read(path="/test/acts/47/6C/1")
        subsection.select(
            TextQuoteSelector(exact="The beardcoin shall be a cryptocurrency")
        )
        assert subsection.means(section)
        assert section >= subsection
        assert not section > subsection
        assert not section.text_sequence() > subsection.text_sequence()

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

    @pytest.mark.vcr()
    def test_no_double_spaces_around_repealed_section(self):
        section = self.client.read(path="/test/acts/47/8/2")
        assert "or  remove the beard with" not in section.text


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

    def test_invalid_selector_text(self, section_11_subdivided):
        section_11_subdivided["selection"] = [
            {"exact": "text that doesn't exist in the code"}
        ]
        schema = EnactmentSchema()
        with pytest.raises(TextSelectionError):
            _ = schema.load(section_11_subdivided)

    def test_select_text_with_string(self, fourth_a):
        schema = EnactmentSchema()
        fourth_a = schema.load(fourth_a)
        fourth_a.select("The right of the people")
        assert fourth_a.selected_text() == "The right of the people..."

    @pytest.mark.vcr()
    def test_select_method_clears_previous_selection(self):
        old_version = self.client.read("/test/acts/47/8/2", date="2015-01-01")
        old_selector = TextPositionSet(TextPositionSelector(start=0, end=65),)
        old_version.select(old_selector)
        assert old_version.selected_text() == (
            "Any such person issued a notice to remedy under subsection 1 must..."
        )

    @pytest.mark.vcr()
    def test_no_space_before_ellipsis(self):
        enactment = self.client.read(path="/us/usc/t17/s102/b")
        enactment.select(TextQuoteSelector(suffix="idea, procedure,"))
        assert " ..." not in enactment.selected_text()


class TestCompareEnactment:
    client = Client(api_token=TOKEN)

    @pytest.mark.vcr()
    def test_equal_enactment_text(self):
        """Test provisions with the same text (different dates)."""
        old_version = self.client.read(path="/test/acts/47/6A", date=date(1999, 1, 1))
        new_version = self.client.read(path="/test/acts/47/6A", date=date(2020, 1, 1))
        assert old_version.means(new_version)

    @pytest.mark.vcr()
    def test_unequal_enactment_text(self):
        fourth_a = self.client.fetch(path="/us/const/amendment/IV")
        search_clause = fourth_a.copy()
        search_clause["selection"] = [{"suffix": ", and no Warrants"}]

        schema = EnactmentSchema()

        fourth_a = schema.load(fourth_a)
        search_clause = schema.load(search_clause)

        assert fourth_a != search_clause
        assert not fourth_a.means(search_clause)
        assert fourth_a >= search_clause

    @pytest.mark.vcr()
    def test_not_gt_if_equal(self):
        enactment = self.client.read(path="/test/acts/47/1", date=date(1999, 1, 1))
        assert enactment == enactment
        assert not enactment > enactment
        assert enactment >= enactment

    @pytest.mark.vcr()
    def test_not_gt_if_equal_with_selection(self):
        search_clause = self.client.read(path="/us/const/amendment/IV")
        search_clause.select(TextQuoteSelector(suffix=", and no Warrants"))

        assert search_clause == search_clause
        assert search_clause.means(search_clause)
        assert not search_clause > search_clause

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
        assert combined.text_sequence() > subdivided.text_sequence()

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
    def test_same_phrase_different_provisions_same_meaning(self):
        amend_5 = self.client.read(path="/us/const/amendment/V")
        amend_14 = self.client.read(path="/us/const/amendment/XIV/1")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        amend_5.select(selector)
        amend_14.select(selector)
        assert amend_5.means(amend_14)

    @pytest.mark.vcr()
    def test_same_phrase_different_provisions_implication(self):
        amend_5 = self.client.read(path="/us/const/amendment/V")
        amend_14 = self.client.read(path="/us/const/amendment/XIV/1")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        amend_5.select(selector)
        amend_14.select(selector)
        assert amend_5 >= amend_14

    @pytest.mark.vcr()
    def test_same_phrase_selected_in_nested_provision_same_meaning(self):
        amend_5 = self.client.read(path="/us/const/amendment/V")
        amend_14 = self.client.read(path="/us/const/amendment/XIV")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        amend_5.select(selector)
        amend_14.select(selector)
        assert amend_5.means(amend_14)

    @pytest.mark.vcr()
    def test_same_phrase_selected_in_nested_provision_implication(self):
        amend_5 = self.client.read(path="/us/const/amendment/V")
        amend_14 = self.client.read(path="/us/const/amendment/XIV")
        selector = TextQuoteSelector(
            exact="life, liberty, or property, without due process of law"
        )
        amend_5.select(selector)
        amend_14.select(selector)
        assert amend_5 >= amend_14

    def test_enactment_does_not_imply_textsequence(self, section_11_subdivided):
        schema = EnactmentSchema()
        subdivided = schema.load(section_11_subdivided)
        text = subdivided.text_sequence()
        assert not subdivided > text

    def test_enactment_does_not_mean_textpassage(self, section_11_subdivided):
        schema = EnactmentSchema()
        subdivided = schema.load(section_11_subdivided)
        text = subdivided.text_sequence()
        assert not subdivided.means(text.passages[0])
        assert not text.passages[0].means(subdivided)


class TestAddEnactments:
    client = Client(api_token=TOKEN)

    @pytest.mark.vcr()
    def test_add_subset_nested_enactment(self):
        """Test that adding an included Enactment returns the same Enactment."""
        greater = self.client.read(path="/test/acts/47/8/2")
        lesser = self.client.read(path="/test/acts/47/8/2/a")
        combined = greater + lesser
        assert combined.means(greater)

    @pytest.mark.vcr()
    def test_add_superset_nested_enactment(self):
        """Test that adding an included Enactment returns the same Enactment."""
        greater = self.client.read(path="/test/acts/47/8/2")
        lesser = self.client.read(path="/test/acts/47/8/2/a")
        combined = lesser + greater
        assert combined.means(greater)

    def test_add_shorter_plus_longer(self, fourth_a):
        search_clause = fourth_a.copy()
        search_clause["selection"] = [{"suffix": ", and no Warrants"}]

        schema = EnactmentSchema()

        fourth_a = schema.load(fourth_a)
        search_clause = schema.load(search_clause)

        greater_plus_lesser = search_clause + fourth_a

        assert greater_plus_lesser.text == fourth_a.text
        assert greater_plus_lesser.means(fourth_a)

        lesser_plus_greater = fourth_a + search_clause
        assert lesser_plus_greater.text == fourth_a.text
        assert lesser_plus_greater.means(fourth_a)

    def test_add_overlapping_text_selection(self, fourth_a):
        schema = EnactmentSchema()
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
        schema = EnactmentSchema()
        left = schema.load(fourth_a)
        right = schema.load(fourth_a)
        left.select("The right of the people to be secure in their persons")
        right.select("shall not be violated")
        left.select_more_text_at_current_node(right.selection)
        assert left.selected_text() == (
            "The right of the people to be secure in their persons..."
            "shall not be violated..."
        )

    def test_select_unavailable_text(self, fourth_a):
        schema = EnactmentSchema()
        fourth = schema.load(fourth_a)
        with pytest.raises(TextSelectionError):
            fourth.select("right to privacy")

    @pytest.mark.vcr()
    def test_add_selection_from_changed_section(self):
        old_version = self.client.read("/test/acts/47/6D/1", date="1935-04-01")
        new_version = self.client.read("/test/acts/47/6D/1", date="2013-07-18")
        old_version.select("bona fide religious")
        new_version.select("reasons.")
        new_version.select_more_text_from_changed_version(old_version)
        assert new_version.selected_text() == "...bona fide religious...reasons."

    @pytest.mark.vcr()
    def test_add_selection_from_changed_node_and_subnode(self):
        """Test that text that has changed subsections can still be added."""
        old_version = self.client.read("/test/acts/47/8/2", date="1935-04-01")
        new_version = self.client.read("/test/acts/47/8/2", date="2013-07-18")
        new_version.select(
            "Any such person issued a notice to remedy under subsection 1 must"
        )
        old_version.select("obtain a beardcoin")
        combined = new_version + old_version
        assert combined.selected_text().endswith("must...obtain a beardcoin...")
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

    @pytest.mark.vcr()
    def test_get_recursive_selection(self):
        old_version = self.client.read("/test/acts/47/8/2", date="2015-01-01")
        old_selector = TextPositionSet(TextPositionSelector(start=0, end=65),)
        old_version.select(old_selector)
        old_version.children[4].select(
            "obtain a beardcoin from the Department of Beards"
        )
        selector_set = old_version.tree_selection()
        ranges = selector_set.ranges()
        assert ranges[0].start == 0
        assert ranges[0].end == 65

        assert ranges[1].start == 218
        assert ranges[1].end == 266

        as_quotes = selector_set.as_quotes(old_version.text)
        assert as_quotes[1].exact == "obtain a beardcoin from the Department of Beards"

    @pytest.mark.vcr()
    def test_add_selection_from_child_node(self):
        old_version = self.client.read("/test/acts/47/8/2", date="2015-01-01")
        old_selector = TextPositionSet(TextPositionSelector(start=0, end=65),)
        old_version.select(old_selector)
        old_version.children[4].select(
            "obtain a beardcoin from the Department of Beards"
        )
        assert old_version.selected_text() == (
            "Any such person issued a notice to remedy under subsection 1 must..."
            "obtain a beardcoin from the Department of Beards..."
        )

        new_version = self.client.read("/test/acts/47/8/2/c", date="2015-01-01")
        new_version.select()

        combined = old_version + new_version

        assert combined.selected_text() == (
            "Any such person issued a notice to remedy under subsection 1 must..."
            "remove the beard with a laser, or "
            "obtain a beardcoin from the Department of Beards..."
        )

    @pytest.mark.vcr()
    def test_add_selection_from_parent_node(self):
        parent_version = self.client.read("/test/acts/47/8/2", date="2015-01-01")
        child_version = self.client.read("/test/acts/47/8/2/c", date="2015-01-01")

        parent_version.select(
            "Any such person issued a notice to remedy under subsection 1 must"
        )
        child_version.select("remove the beard with a laser")

        combined = child_version + parent_version
        assert combined.selected_text() == (
            "Any such person issued a notice to remedy under subsection 1 must..."
            "remove the beard with a laser..."
        )
        # original Enactments should be unchanged
        assert (
            parent_version.selected_text()
            == "Any such person issued a notice to remedy under subsection 1 must..."
        )
        assert child_version.selected_text() == "remove the beard with a laser..."

    @pytest.mark.vcr()
    def test_fail_to_add_repeated_text_from_changed_version(self):
        """Fail to place selection because "Department of Beards" occurs twice in this scope."""
        new_version = self.client.read("/test/acts/47/8")
        new_version.select(
            TextQuoteSelector(
                prefix="Department of Beards, ", exact="Australian Federal Police"
            )
        )

        old_version = self.client.read("/test/acts/47/8", date="1935-04-01")
        old_version.select(
            TextQuoteSelector(prefix="officer of the ", exact="Department of Beards")
        )

        with pytest.raises(ValueError):
            _ = new_version + old_version

    @pytest.mark.vcr()
    def test_fail_to_add_non_parent_or_child_enactment(self):
        left = self.client.read("/test/acts/47/1")
        right = self.client.read("/test/acts/47/2")
        with pytest.raises(ValueError):
            _ = left + right

    @pytest.mark.vcr()
    def test_fail_to_add_text_not_in_this_version(self):
        """Fail to add selection from new version because it isn't in the old version."""
        old_version = self.client.read("/test/acts/47/8", date="1935-04-01")
        new_version = self.client.read("/test/acts/47/8")

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

    @pytest.mark.vcr()
    def test_fail_to_add_node_not_in_this_version(self):
        """Fail to add new selection because its node isn't in the old version."""
        old_version = self.client.read("/test/acts/47/8/2", date="1935-04-01")
        new_version = self.client.read("/test/acts/47/8/2/c")
        with pytest.raises(ValueError):
            _ = old_version + new_version

    @pytest.mark.vcr()
    @pytest.mark.xfail()
    def test_locate_anchor_by_remembering_prefix(self):
        """
        Place position selector by remembering prefix from TextQuoteSelector.

        Xfails because the prefix information is lost when the selector
        becomes a position selector.
        """
        new_version = self.client.read("/test/acts/47/8")
        new_version.select(
            TextQuoteSelector(
                prefix="Department of Beards, ", exact="Australian Federal Police"
            )
        )

        old_version = self.client.read("/test/acts/47/8", date="1935-04-01")
        old_version.select(
            TextQuoteSelector(prefix="officer of the ", exact="Department of Beards")
        )

        combined = new_version + old_version
        assert combined.text == "...Department of Beards...Australian Federal Police..."

    @pytest.mark.vcr()
    def test_able_to_add_subsection_with_text_repeated_elsewhere(self):
        new_version = self.client.read("/test/acts/47/8")
        new_version.select(
            TextQuoteSelector(
                prefix="Department of Beards, ", exact="Australian Federal Police"
            )
        )

        old_version = self.client.read("/test/acts/47/8", date="1935-04-01")
        old_version.select(
            TextQuoteSelector(prefix="officer of the ", exact="Department of Beards")
        )

        new_version.children[0].select_more_text_from_changed_version(
            old_version.children[0]
        )

        assert (
            new_version.selected_text()
            == "...Department of Beards...Australian Federal Police..."
        )

    def test_add_string_as_selector(self, section_11_subdivided):
        schema = EnactmentSchema()
        section = schema.load(section_11_subdivided)
        section.select("The Department of Beards may issue licenses to such")
        more = section + "hairdressers"
        assert (
            more.selected_text()
            == "The Department of Beards may issue licenses to such...hairdressers..."
        )


class TestConsolidateEnactments:
    """Test function for combining a list of Enactments."""

    client = Client(api_token=TOKEN)

    def test_consolidate_enactments(self, fourth_a):
        search_clause = fourth_a.copy()
        search_clause["selection"] = [{"suffix": ", and no Warrants"}]

        warrants_clause = fourth_a.copy()
        warrants_clause["selection"] = [{"prefix": "shall not be violated,"}]

        schema = EnactmentSchema()

        fourth = schema.load(fourth_a)
        search = schema.load(search_clause)
        warrants = schema.load(warrants_clause)

        consolidated = consolidate_enactments([fourth, search, warrants])
        assert len(consolidated) == 1
        assert consolidated[0].means(fourth)

    @pytest.mark.vcr()
    def test_consolidate_adjacent_passages(self):
        copyright_clause = self.client.read("/us/const/article/I/8/8")
        copyright_statute = self.client.read("/us/usc/t17/s102/b")

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
            and law.selected_text().endswith("their respective Writings...")
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

