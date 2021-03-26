from copy import deepcopy

import pytest

from legislice.groups import EnactmentGroup


class TestEnactmentGroups:
    def test_make_group(self, copyright_clause, copyright_statute):
        group = EnactmentGroup([copyright_clause, copyright_statute])
        assert len(group) == 2
        assert isinstance(EnactmentGroup(group), EnactmentGroup)

    def test_consolidate_adjacent_passages(self, copyright_clause, copyright_statute):
        copyright_clause.select(None)
        securing_for_authors = copyright_clause + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        and_inventors = copyright_clause + "and Inventors"
        right_to_writings = (
            copyright_clause + "the exclusive Right to their respective Writings"
        )
        left = EnactmentGroup([and_inventors, copyright_statute])
        right = EnactmentGroup([securing_for_authors, right_to_writings])

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
        with pytest.raises(TypeError):
            EnactmentGroup([cite])


class TestImplies:
    def test_no_implication_of_group(self, copyright_clause, copyright_statute):
        extra = deepcopy(copyright_clause)
        extra.select(None)
        securing_for_authors = extra + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        and_inventors = extra + "and Inventors"
        left = EnactmentGroup(copyright_clause)
        right = EnactmentGroup([securing_for_authors, and_inventors, copyright_statute])
        assert not left.implies(right)

    def test_implication_of_group(self, copyright_clause, copyright_statute):
        extra = deepcopy(copyright_clause)
        extra.select(None)
        securing_for_authors = extra + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        and_inventors = extra + "and Inventors"
        left = EnactmentGroup([copyright_clause, copyright_statute])
        right = EnactmentGroup([securing_for_authors, and_inventors])
        assert left.implies(right)
        assert left >= right

    def test_implication_of_enactment(self, copyright_clause, copyright_statute):
        extra = deepcopy(copyright_clause)
        extra.select(None)
        securing_for_authors = extra + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        left = EnactmentGroup([copyright_clause, copyright_statute])
        assert left > securing_for_authors


class TestAdd:
    def test_add_enactment_to_group(self, copyright_clause):
        copyright_clause.select(None)
        securing_for_authors = copyright_clause + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        and_inventors = copyright_clause + "and Inventors"
        right_to_writings = (
            copyright_clause + "the exclusive Right to their respective Writings"
        )
        left = EnactmentGroup([securing_for_authors, and_inventors])
        right = right_to_writings
        result = left + right
        assert len(result) == 1
        assert "respective Writings…" in str(result)
        assert "/us/const/article/I/8/8" in str(result[0])
        assert "1788-09-13" in str(result[:])

    def test_add_empty_group(self, copyright_clause, copyright_statute):
        copyright_clause.select(None)
        securing_for_authors = copyright_clause + (
            "To promote the Progress of Science and "
            "useful Arts, by securing for limited Times to Authors"
        )
        writings = copyright_clause + "their respective Writings"
        left = EnactmentGroup([securing_for_authors, writings, copyright_statute])
        assert len(left) == 2
        right = EnactmentGroup(None)
        result = left + right
        assert len(result) == 2

    def test_enactments_ordered_after_adding_groups(self, first_a, second_a, third_a):
        establishment_clause = deepcopy(first_a)
        establishment_clause.select(
            "Congress shall make no law respecting an establishment of religion"
        )
        speech_clause = deepcopy(first_a)
        speech_clause.select(
            ["Congress shall make no law", "abridging the freedom of speech"]
        )

        arms_clause = deepcopy(second_a)
        arms_clause.select(
            "the right of the people to keep and bear arms, shall not be infringed."
        )
        third_amendment = deepcopy(third_a)

        left = EnactmentGroup([establishment_clause, arms_clause])
        right = EnactmentGroup([third_amendment, speech_clause])

        combined = left + right
        assert len(combined) == 3
        assert combined[0].node == "/us/const/amendment/I"
