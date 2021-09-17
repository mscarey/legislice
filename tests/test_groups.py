from copy import deepcopy
from datetime import date

from pydantic import ValidationError
import pytest

from legislice.enactments import Enactment
from legislice.groups import EnactmentGroup


class TestEnactmentGroups:
    def test_make_group(self, copyright_clause, copyright_statute):
        group = EnactmentGroup(passages=[copyright_clause, copyright_statute])
        assert len(group) == 2
        assert isinstance(EnactmentGroup(passages=group), EnactmentGroup)

    def test_consolidate_adjacent_passages(self, copyright_clause, copyright_statute):

        passage = copyright_clause.select(None)
        securing_for_authors = passage + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        and_inventors = passage + "and Inventors"
        right_to_writings = passage + "the exclusive Right to their respective Writings"
        left = EnactmentGroup(passages=[and_inventors, copyright_statute])
        right = EnactmentGroup(passages=[securing_for_authors, right_to_writings])

        combined = left + right
        assert len(combined) == 2
        assert "/us/usc/t17/s102/b" in repr(combined)
        assert any(
            law.selected_text().startswith("To promote the Progress")
            and law.selected_text().endswith("their respective Writings…")
            for law in combined
        )

    def test_wrong_type_in_group(self, section6d, test_client):
        section = test_client.read_from_json(section6d)
        cite = section.as_citation()
        with pytest.raises(ValidationError):
            EnactmentGroup(passages=[cite])


class TestImplies:
    def test_no_implication_of_group(self, copyright_clause, copyright_statute):
        extra = deepcopy(copyright_clause)
        passage = extra.select(None)
        securing_for_authors = passage + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        and_inventors = passage + "and Inventors"
        left = EnactmentGroup(passages=copyright_clause)
        right = EnactmentGroup(
            passages=[securing_for_authors, and_inventors, copyright_statute]
        )
        assert not left.implies(right)

    def test_implication_of_group(self, copyright_clause, copyright_statute):
        extra = deepcopy(copyright_clause)
        passage = extra.select(None)
        securing_for_authors = passage + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        and_inventors = passage + "and Inventors"
        left = EnactmentGroup(passages=[copyright_clause, copyright_statute])
        right = EnactmentGroup(passages=[securing_for_authors, and_inventors])
        assert left.implies(right)
        assert left >= right

    def test_implication_of_enactment(self, copyright_clause, copyright_statute):
        extra = deepcopy(copyright_clause)
        passage = extra.select(None)
        securing_for_authors = passage + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        left = EnactmentGroup(passages=[copyright_clause, copyright_statute])
        assert left > securing_for_authors


class TestAdd:
    def test_add_enactment_to_group(self, copyright_clause):
        passage = copyright_clause.select(None)
        securing_for_authors = passage + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        and_inventors = passage + "and Inventors"
        right_to_writings = passage + "the exclusive Right to their respective Writings"
        left = EnactmentGroup(passages=[securing_for_authors, and_inventors])
        right = right_to_writings
        result = left + right
        assert len(result) == 1
        assert "respective Writings…" in str(result)
        assert "/us/const/article/I/8/8" in str(result[0])
        assert "1788-09-13" in str(result[:])

    def test_add_empty_group(self, copyright_clause, copyright_statute):
        passage = copyright_clause.select(None)
        securing_for_authors = passage + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        writings = passage + "their respective Writings"
        left = EnactmentGroup(
            passages=[securing_for_authors, writings, copyright_statute]
        )
        assert len(left) == 2
        right = EnactmentGroup()
        result = left + right
        assert len(result) == 2

    def test_enactments_ordered_after_adding_groups(self, first_a, second_a, third_a):
        establishment_clause = first_a.select(
            "Congress shall make no law respecting an establishment of religion"
        )
        speech_clause = first_a.select(
            ["Congress shall make no law", "abridging the freedom of speech"]
        )

        arms_clause = second_a.select(
            "the right of the people to keep and bear arms, shall not be infringed."
        )

        left = EnactmentGroup(passages=[establishment_clause, arms_clause])
        right = EnactmentGroup(passages=[third_a, speech_clause])

        combined = left + right
        assert len(combined) == 3
        assert combined[0].node == "/us/const/amendment/I"

    def test_sort_enactments_in_group(self, copyright_clause, copyright_statute):
        regulation = Enactment(
            node="/us/cfr/t37/s202.1",
            heading="",
            start_date=date(1992, 2, 21),
            text_version="The following are examples of works not subject to copyright",
        )
        group = EnactmentGroup(
            passages=[regulation, copyright_clause, copyright_statute]
        )
        assert group[-1].node == "/us/cfr/t37/s202.1"

    def test_sort_state_enactment_in_group(self, copyright_clause, copyright_statute):
        regulation = Enactment(
            node="/us/cfr/t37/s202.1",
            heading="",
            start_date=date(1992, 2, 21),
            text_version="The following are examples of works not subject to copyright",
        )
        ca_statute = Enactment(
            node="/us-ca/code/evid/s351",
            start_date=date(1966, 1, 1),
            text_version="Except as otherwise provided by statute, all relevant evidence is admissible.",
            heading="",
        )
        group = EnactmentGroup(
            passages=[regulation, ca_statute, copyright_clause, copyright_statute]
        )
        assert group[-1].node == "/us-ca/code/evid/s351"
