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
