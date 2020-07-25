from datetime import date

from legislice.schemas import EnactmentSchema
from legislice.name_index import EnactmentIndex


class TestIndexEnactment:
    def test_index_section_with_name(self, section6d):
        mentioned = EnactmentIndex()
        section6d["name"] = "section6d"
        mentioned.index_enactment(section6d)
        assert mentioned["section6d"]["start_date"] == "1935-04-01"
