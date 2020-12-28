import pytest

from legislice import Enactment


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
        serialized = cite.as_dict()
        assert serialized["type"] == "legislation"

    def test_csl_format_container_title(self, section6d, test_client):
        section = test_client.read_from_json(section6d)
        cite = section.as_citation()
        serialized = cite.as_dict()
        assert serialized["container-title"] == "Test Acts"

    @pytest.mark.vcr
    def test_csl_format_no_revision_date(self, test_client):
        """Citation for provision with no known revision date in the database."""
        section = test_client.read("/us/usc/t17/s103/b")
        cite = section.as_citation()
        serialized = cite.as_dict()
        assert str(cite) == "17 U.S. Code sec. 103"
        assert serialized.get("event-date") is None
        assert serialized.get("revision_date") is None

    def test_csl_format_with_revision_date(self, section_11_subdivided, test_client):
        """Citation for provision with a revision date in the database."""
        section = test_client.read_from_json(section_11_subdivided)
        cite = section.as_citation()
        serialized = cite.as_dict()
        assert str(cite) == "47 Test Acts sec. 11 (2013-07-18)"
        assert serialized.get("event-date") == {"date-parts": [["2013", 7, 18]]}
        assert serialized.get("revision_date") is None
