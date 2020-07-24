from datetime import date

from legislice.schemas import EnactmentSchema
from legislice.text_expansion import Mentioned


class TestExpandEnactment:
    def test_expand_enactment_from_name(self, section6d):
        section6d["name"] = "section6d"
        to_load = [section6d, "section6d"]
        schema = EnactmentSchema(many=True)
        loaded = schema.load(to_load)
        assert loaded.start_date == date(1935, 4, 1)
