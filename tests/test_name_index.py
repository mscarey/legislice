from datetime import date

from legislice.schemas import EnactmentSchema
from legislice.name_index import EnactmentIndex, collect_enactments


class TestIndexEnactments:
    def test_index_section_with_name(self, section6d):
        mentioned = EnactmentIndex()
        section6d["name"] = "section6d"
        mentioned.index_enactment(section6d)
        assert mentioned["section6d"]["start_date"] == "1935-04-01"


class TestCollectEnactments:
    """Tests for finding and collecting Enactment records from a nested dict."""

    example_rules = [
        {
            "inputs": [
                {"type": "fact", "content": "{the suspected beard} was facial hair"},
                {
                    "type": "fact",
                    "content": "the length of the suspected beard was >= 5 millimetres",
                },
                {
                    "type": "fact",
                    "content": "the suspected beard occurred on or below the chin",
                },
            ],
            "outputs": [
                {
                    "type": "fact",
                    "content": "the suspected beard was a beard",
                    "name": "the fact that the facial hair was a beard",
                }
            ],
            "enactments": [
                {
                    "node": "/test/acts/47/4",
                    "exact": "In this Act, beard means any facial hair no shorter than 5 millimetres in length that:",
                    "name": "beard means",
                },
                {"node": "/test/acts/47/4/a", "suffix": ", or"},
            ],
            "universal": True,
        },
        {
            "inputs": [
                {"type": "fact", "content": "{the suspected beard} was facial hair"},
                {
                    "type": "fact",
                    "content": "the length of the suspected beard was >= 5 millimetres",
                },
                {
                    "type": "fact",
                    "content": "the suspected beard existed in an uninterrupted line from the front of one ear to the front of the other ear below the nose",
                },
            ],
            "outputs": [
                {
                    "type": "fact",
                    "content": "the suspected beard was a beard",
                    "name": "the fact that the facial hair was a beard",
                }
            ],
            "enactments": ["beard means", {"node": "/test/acts/47/4/b"}],
            "universal": True,
        },
    ]

    def test_collect_enactments_from_list(
        self, section6d, section_11_subdivided, fifth_a
    ):
        section_11_subdivided["name"] = "s11"
        section6d["name"] = "6c"
        fifth_a["name"] = "5a"
        obj, mentioned = collect_enactments([section6d, section_11_subdivided, fifth_a])
        schema = EnactmentSchema()
        mentioned_entry = mentioned.get_by_name("5a")
        enactment = schema.load(mentioned_entry)
        assert enactment.start_date == date(1791, 12, 15)

    def test_collect_enactments_from_dict(self):
        obj, mentioned = collect_enactments(self.example_rules)
        assert mentioned["beard means"]["node"] == "/test/acts/47/4"

    def test_replace_enactment_in_source_with_name(self):
        example_rules, mentioned = collect_enactments(self.example_rules)
        assert example_rules[0]["enactments"][0] == "beard means"
        assert example_rules[0]["enactments"][1] == '/test/acts/47/4/a:suffix=", or"'
