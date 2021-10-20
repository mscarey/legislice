import pytest

from legislice import Citation


class TestMakeCitation:
    def test_bad_jurisdiction(self):
        with pytest.raises(KeyError):
            Citation(jurisdiction="atlantis", code="acts")

    def test_bad_code(self):
        with pytest.raises(KeyError):
            Citation(jurisdiction="us", code="proclamations")


class TestSerializeCitation:
    def test_make_citation_object(self, section6d, test_client):
        section = test_client.read_from_json(section6d)
        cite = section.as_citation()
        assert cite.revision_date.isoformat() == "1935-04-01"

    def test_constitutional_cite_not_implemented(self, fifth_a, test_client):
        amendment_5 = test_client.read_from_json(fifth_a)
        with pytest.raises(NotImplementedError):
            amendment_5.as_citation()

    def test_csl_format_citation_type(self, section6d, test_client):
        section = test_client.read_from_json(section6d)
        cite = section.as_citation()
        serialized = cite.csl_dict()
        assert serialized["type"] == "legislation"

    def test_csl_format_container_title(self, section6d, test_client):
        section = test_client.read_from_json(section6d)
        cite = section.as_citation()
        serialized = cite.csl_dict()
        assert serialized["container-title"] == "Test Acts"

    def test_csl_format_with_revision_date(self, section_11_subdivided, test_client):
        """Citation for provision with a revision date in the database."""
        section = test_client.read_from_json(section_11_subdivided)
        cite = section.as_citation()
        serialized = cite.csl_dict()
        assert str(cite) == "47 Test Acts § 11 (2013)"
        assert serialized.get("event-date") == {"date-parts": [["2013", 7, 18]]}
        assert serialized.get("revision_date") is None

    @pytest.mark.vcr
    def test_csl_format_no_revision_date(self, test_client):
        """
        Citation for provision with no known revision date in the database.

        The citation depth is limited to the section level.
        """
        section = test_client.read("/us/usc/t17/s103/b")
        cite = section.as_citation()
        serialized = cite.dict()
        assert str(cite).startswith("17 U.S. Code § 103")
        assert serialized.get("event-date") is None
        assert serialized.get("revision_date") is None

    @pytest.mark.vcr
    def test_usc_provision_with_revision_date(self, test_client):
        cares_act = test_client.read("/us/usc/t15/s9021/a/3/B/")
        cite = cares_act.as_citation()
        serialized = cite.csl_dict()
        assert str(cite) == "15 U.S. Code § 9021 (2020)"
        assert serialized["event-date"]["date-parts"][0] == ["2020", 4, 10]

    def test_citation_for_nested_provision(self, test_client, section_11_subdivided):
        """
        Both citations should be the same because of the CSL JSON format
        doesn't distinguish between citations below the section level.
        """
        section = test_client.read_from_json(section_11_subdivided)
        cite_json = section.as_citation().csl_dict()
        subsection_cite_json = section.children[0].as_citation().csl_dict()
        assert cite_json["section"] == subsection_cite_json["section"]
