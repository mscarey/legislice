from legislice.groups import EnactmentGroup


class TestEnactmentGroups:
    def test_make_group(self, test_client):
        copyright_clause = test_client.read("/us/const/article/I/8/8")
        copyright_statute = test_client.read("/us/usc/t17/s102/b")
        group = EnactmentGroup([copyright_clause, copyright_statute])
        assert len(group) == 2

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
        left = EnactmentGroup([and_inventors, copyright_statute])
        right = EnactmentGroup([securing_for_authors, right_to_writings])

        combined = left + right
        assert len(combined) == 2
        assert any(
            law.selected_text().startswith("To promote the Progress")
            and law.selected_text().endswith("their respective Writings…")
            for law in combined
        )
